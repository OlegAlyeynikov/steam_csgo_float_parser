from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic, View
from task_manager.models import Worker
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from task_manager.utils import start_child_processes
from django.conf import settings
from dotenv import load_dotenv
import subprocess
import time
import json
from django.core.files.storage import FileSystemStorage
import os
import psutil
import csv

web_data = settings.WEB_GLOBAL_DATA
load_dotenv()


class LastPurchasesView(View):
    template_name = 'task_manager/last_purchases.html'

    def get(self, request, *args, **kwargs):
        # Read the last 5 lines from the CSV file
        last_purchases = self.get_last_purchases()

        return render(request, self.template_name, {'last_purchases': last_purchases})

    def get_last_purchases(self):
        csv_file_path = os.getenv("PATH_TO_BUY_ITEMS_CSV_DB")  # Update with your actual file path

        # Read the last 5 lines from the CSV file
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            lines = list(csv.reader(file))
            last_5_lines = lines[-5:]
            print(last_5_lines)

        return last_5_lines


class GetIPView(View):
    def get(self, request):
        client_ip = self.get_client_ip(request)
        request.session['client_ip'] = client_ip
        return JsonResponse({'client_ip': client_ip})

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name

        # Specify the target folder
        target_folder = os.getenv("PATH_TO_UPLOAD_DIRECTORY")  # Change this to your desired folder name
        target_folder_path = os.path.join(settings.MEDIA_ROOT, target_folder)

        # Create the target folder if it doesn't exist
        os.makedirs(target_folder_path, exist_ok=True)

        # Check if a file with the same name exists in the target folder
        existing_file_path = os.path.join(target_folder_path, file_name)
        if os.path.exists(existing_file_path):
            os.remove(existing_file_path)

        fs = FileSystemStorage(location=target_folder_path)
        filename = fs.save(file_name, uploaded_file)
        file_url = fs.url(filename)
        return render(request, 'task_manager/upload_file.html', {'file_url': file_url})

    return render(request, 'task_manager/upload_file.html')


@login_required
def save_proxy(request):
    if request.method == 'POST':
        content = request.POST.get('proxy_content', '')
        file_path = os.getenv("PATH_TO_PROXY_LIST")
        with open(file_path, 'w') as file:
            file.write(content)

    return HttpResponseRedirect('/proxy/')


@login_required
def home_view(request):
    file_path = os.getenv("PATH_TO_PROXY_LIST")
    with open(file_path, 'r') as file:
        content = file.read()
    proxy_count = content.count('\n') + 1
    return render(request, 'task_manager/home.html', {'proxy_count': proxy_count})


@login_required
def proxy_view(request):
    # Read the file
    file_path = os.getenv("PATH_TO_PROXY_LIST")
    with open(file_path, 'r') as file:
        content = file.read()
    proxy_count = content.count('\n') + 1
    # Render proxy.html with the file content
    return render(request, 'task_manager/proxy.html', {'proxy_count': proxy_count, 'file_content': content})


@login_required
def items_view(request):
    # Read the file
    file_path = os.getenv("PATH_TO_CONDITIONS")
    with open(file_path, 'r') as file:
        content = file.read()
    # Render proxy.html with the file content
    return render(request, 'task_manager/items.html', {'file_content': content})


def items_save(request):
    if request.method == 'POST':
        content = request.POST.get('items_content', '')
        file_path = os.getenv("PATH_TO_CONDITIONS")
        # Save the edited content back to the file
        with open(file_path, 'w') as file:
            file.write(content)

    return HttpResponseRedirect('/items/')


@login_required
class HomeView(TemplateView):
    template_name = 'task_manager/home.html'

    def form_valid(self, form):
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class ProcessManager:
    def __init__(self):
        pass

    def get_process_status_by_port(self, port):
        for process in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                if process.info and 'name' in process.info and 'python' in process.info['name'].lower():
                    if process.info and 'connections' in process.info and process.info['connections']:
                        for conn in process.info['connections']:
                            if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                                return True  # Процесс найден по порту
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False


class ControlView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_main = os.getenv('PATH_TO_SEARCH_MAIN')
        self.listing_main = os.getenv('PATH_TO_LISTING_MAIN')
        self.buy_module_main = os.getenv('PATH_TO_BUY_MODULE_MAIN')

        self.buy_module_venv = os.getenv('PATH_TO_BUY_MODULE_VENV')
        self.listing_module_venv = os.getenv('PATH_TO_LISTING_MODULE_VENV')
        self.search_module_venv = os.getenv('PATH_TO_SEARCH_MODULE_VENV')

        self.processes = [
            (self.search_main, self.search_module_venv, int(os.getenv("SEARCH_PORT")), 3),
            (self.listing_main, self.listing_module_venv, int(os.getenv("LISTING_PORT")), 1),
            (self.buy_module_main, self.buy_module_venv, int(os.getenv("BUY_MODULE_PORT")), 0),
        ]
        self.web_data_update = {
            "proxy_nowork_count": 0,
            "proxy_work_count": 0,
            "proxy_slow": 0,
            "proxy_bad": 0,
            "buy_ok": 0,
            "buy_error": 0,
            "amount_proxies": 0,
        }

    template_name = 'control.html'
    process_manager = ProcessManager()

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        command = request.POST.get('command')

        if command:
            if command == 'start':
                start_child_processes(self.processes)
                return JsonResponse({'status': 'success'})

            elif command in ['stop', 'restart']:
                subprocess.run(['pkill', '-f', self.search_main])
                time.sleep(5)
                subprocess.run(['pkill', '-f', self.listing_main])
                time.sleep(5)
                subprocess.run(['pkill', '-f', self.buy_module_main])
                time.sleep(5)

                if command == 'restart':
                    time.sleep(8)
                    start_child_processes(self.processes)
                    time.sleep(10)

                web_data.update(self.web_data_update)
                return JsonResponse({'status': 'success'})

        return JsonResponse({'status': 'error', 'message': 'Invalid command'})


@csrf_exempt
def update_data(request):
    try:
        if request.method == 'POST':
            try:
                request_data = json.loads(request.body.decode('utf-8'))

                for key in ['proxy_bad', 'proxy_slow', 'balance', 'buy_ok', 'buy_error', 'items_count',
                            'proxy_work_count', 'buy_items', 'listing_proxy_work', 'search_proxy_work',
                            'len_listing_sessions', 'len_search_sessions', 'proxy_nowork_count', 'amount_proxies']:
                    if key in request_data:
                        web_data[key] = request_data[key]

                return JsonResponse(web_data)

            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
        else:
            return JsonResponse({'error': 'NO POST :( '})

    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def home_status(request):
    if request.method == 'GET':
        process_manager = ProcessManager()
        web_data['port_8088'] = process_manager.get_process_status_by_port(int(os.getenv("RUN_SERVER_PORT")))
        web_data['port_12352'] = process_manager.get_process_status_by_port(int(os.getenv("SEARCH_PORT")))
        web_data['port_12350'] = process_manager.get_process_status_by_port(int(os.getenv("LISTING_PORT")))
        web_data['port_12351'] = process_manager.get_process_status_by_port(int(os.getenv("BUY_MODULE_PORT")))

        # print(f"GET: SOFT STATUS{web_data}")
        soft_status = web_data.copy()
        if 'buy_items' in web_data:
            del web_data['buy_items']
        return JsonResponse(soft_status)
    else:
        return JsonResponse({'error': 'Invalid request method'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "Logged out successfully.")
        return redirect("login")


class WorkerListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    template_name = "task_manager/worker_list.html"
    context_object_name = "worker_list"
    paginate_by = 40
    queryset = Worker.objects.all()
