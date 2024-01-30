from django.urls import path
from task_manager.views import (WorkerListView, home_view, ControlView, proxy_view, save_proxy, items_view,
                                items_save, home_status, update_data, LogoutView, upload_file, GetIPView,
                                LastPurchasesView)

urlpatterns = [
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path('', home_view, name='home'),
    path('control/', ControlView.as_view(), name='control'),
    path('proxy/', proxy_view, name='proxy'),
    path('save_proxy/', save_proxy, name='save_proxy'),
    path('items/', items_view, name='items'),
    path('items_save/', items_save, name='items_save'),
    path('home_status/', home_status, name='home_status'),
    path('update_data/', update_data, name='update_data'),
    path('upload_file/', upload_file, name='upload_file'),
    path('get_ip/', GetIPView.as_view(), name='get_ip'),
    path('last_purchases/', LastPurchasesView.as_view(), name='last_purchases'),
]

app_name = "task_manager"
