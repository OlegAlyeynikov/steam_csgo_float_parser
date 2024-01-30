from factory_new import conditions
from tags_730 import Tags

Links_ = []
Base_url = f"https://steamcommunity.com/market/search/render/?query=&appid=730&start=0&count=100&norender=1&l=english"


def get_category_730_quality_tag(index_url: int, hash_name: str, type_asset: str) -> str:
    quality_category = {"StatTrak™": "unusual_strange", "★": "unusual", "★ StatTrak™": "strange"}
    for key, value in quality_category.items():

        if key in hash_name or key in type_asset:
            string_quality_tag = f"&category_730_Quality[{index_url}]=tag_{key}"
            return string_quality_tag
        # string_quality_tag = f"&category_730_Quality[{index_url}]=tag_normal"
        # print(f"No matches quality tags for link index: {index_url}")
    return "&category_730_Quality[]=tag_normal"


def get_category_730_rarity_tag(index_url: int, type_asset: str) -> str:
    tags = Tags["facets"]["730_Rarity"]["tags"]
    if index_url >= 1000:
        index_url = ""
    for key, value in tags.items():
        if value["localized_name"] in type_asset:
            string_rarity_tag = f"&category_730_Rarity[{index_url}]=tag_{key}"
            return string_rarity_tag
    print(f"No matches rarity tags for link index: {index_url}")


def get_category_730_weapon_tag(index_url: int, hash_name: str) -> str:
    tags = Tags["facets"]["730_Weapon"]["tags"]
    for key, value in tags.items():
        if value["localized_name"] in hash_name:
            string_weapon_tag = f"&category_730_Weapon[{index_url}]=tag_{key}"
            return string_weapon_tag
    print(f"No matches weapon tags for link index: {index_url}")


def get_category_730_item_set_collection_tag(index_url: int, collection_name: list) -> str:
    tags = Tags["facets"]["730_ItemSet"]["tags"]
    for key, value in tags.items():
        if value["localized_name"] == collection_name:
            string_item_set_collection_tag = f"&category_730_ItemSet[{index_url}]=tag_{key}"
            return string_item_set_collection_tag
    print(f"No matches item collection tags for link index: {index_url}")


def get_category_730_exterior_tag(index_url: int, exterior: str) -> str:
    if index_url >= 1000:
        index_url = ""
    tags = Tags["facets"]["730_Exterior"]["tags"]
    for key, value in tags.items():
        if value["localized_name"] in exterior:
            string_exterior_tag = f"&category_730_Exterior[{index_url}]=tag_{key}"
            return string_exterior_tag
    print(f"No matches exterior tags for link index: {index_url}")


def get_category_730_type_tag(index_url: int, type_: str) -> str:
    tags = Tags["facets"]["730_Type"]["tags"]
    for key, value in tags.items():
        if "Sniper Rifle" in type_:
            type_sniper = "Sniper Rifle"
            if value["localized_name"] == type_sniper:
                string_type_tag_ = f"&category_730_Type[{index_url}]=tag_{key}"
                return string_type_tag_
        elif value["localized_name"] in type_:
            string_type_tag = f"&category_730_Type[{index_url}]=tag_{key}"
            return string_type_tag
    print(f"No matches type tags for link index: {index_url}")
# ("https://steamcommunity.com/market/listings/730/CZ75-Auto%20%7C%20Syndicate%20%28Factory%20New%29",
#      "0, 0.001, 10000, 680, 900", "CZ75-Auto | Syndicate", "Restricted Pistol", "The 2021 Train Collection",
#      "Factory New"),


def main(index_: int, item_condition: tuple, quality_tag) -> str:

    market_name_ = item_condition[2]
    rarity_and_type_ = item_condition[3]
    item_set_collection = item_condition[4]
    exterior = item_condition[5]

    string_rarity_tag_ = get_category_730_rarity_tag(index_, rarity_and_type_)
    string_weapon_tag_ = get_category_730_weapon_tag(index_, market_name_)
    string_item_set_collection_tag_ = get_category_730_item_set_collection_tag(index_, item_set_collection)
    string_exterior_tag_ = get_category_730_exterior_tag(index_, exterior)
    # string_type_tag_ = get_category_730_type_tag(index_, rarity_and_type_)
    if quality_tag:
        return string_item_set_collection_tag_ + string_weapon_tag_ + string_rarity_tag_
    else:
        string_quality_tag_ = get_category_730_quality_tag(index_, market_name_, rarity_and_type_)
        return string_quality_tag_ + string_item_set_collection_tag_ + string_weapon_tag_ + string_rarity_tag_


def divide_list(input_list, max_chunk_size=50):
    """
    Divide a list into sublists of equal length, each not exceeding the specified maximum size.

    Parameters:
    - input_list: The original list.
    - max_chunk_size: The maximum size of each sublist (default is 50).

    Returns:
    A list of sublists.
    """
    input_length = len(input_list)
    num_chunks = -(-input_length // max_chunk_size)  # Equivalent to math.ceil(input_length / max_chunk_size)
    chunk_size = -(-input_length // num_chunks)  # Round up to ensure equal or smaller-sized chunks

    return [input_list[i:i + chunk_size] for i in range(0, input_length, chunk_size)]


# Function to organize tuples into different lists based on a condition
def organize_items_by_condition(input_list, condition_index):
    tags = Tags["facets"]["730_Rarity"]["tags"]
    organized_lists = {}
    for item_ in input_list:
        condition_value = item_[condition_index]
        for key, value in tags.items():
            local_name = value["localized_name"]
            if local_name in condition_value:
                if local_name not in organized_lists:
                    organized_lists[local_name] = []
                organized_lists[local_name].append(item_)
    return organized_lists


def get_tag_link(condition_index):  # condition_index = 3 Rarity
    global Base_url
    market_name = conditions[0][2]
    rarity_and_type = conditions[0][3]
    exterior = conditions[0][5]
    print(exterior)
    exterior_tag = get_category_730_exterior_tag(1000, exterior)
    tag_links = []
    string_quality_tag = get_category_730_quality_tag(1000, market_name, rarity_and_type)
    if string_quality_tag == "&category_730_Quality[]=tag_normal":
        Base_url = Base_url + string_quality_tag + exterior_tag
    else:
        string_quality_tag = None
        Base_url = Base_url + exterior_tag
    # Organize items based on items[3]
    result = organize_items_by_condition(conditions, condition_index)
    print("Result dict organized by rarity:")
    print(result)
    for condition_value_, item_list in result.items():
        divided_list = divide_list(item_list)
        for list_ in divided_list:
            rarity = condition_value_
            rarity_tag = get_category_730_rarity_tag(1000, rarity)
            print(f"Items with condition rarity value {condition_value_}:")
            Base_url = Base_url + rarity_tag
            hash_name_list = []
            for index_, item in enumerate(list_):
                hash_name_ = item[2] + " (" + item[5] + ")"
                print(hash_name_)
                hash_name_list.append(hash_name_)
                link_tag = main(index_, item, string_quality_tag)
                Base_url += link_tag
            tag_links.append(Base_url)
            print(f"Amount of items: {len(hash_name_list)}")
            print(Base_url)
    print(f"Amount of tag links: {len(tag_links)}")
    print(tag_links)
    return tag_links


if __name__ == "__main__":
    tags_list = get_tag_link(3)
    amount_proxy = len(tags_list) * 120 + len(conditions) * 4
    print(f"Amount of proxies needed: {amount_proxy}")
