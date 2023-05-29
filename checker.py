import requests
import json
import os

def check_failed(config, session):
    if "failed_type" in config:
        failed_type_logic = config.get("failed_type_logic", "and")
        test_urls = config.get("test_urls", [])
        if not test_urls:  
            test_urls = [config.get("test_url", "")]
        results = []
        for test_url in test_urls:
            response = session.get(test_url, timeout=10)
            if config["failed_type"] == "text":
                results.append(any(text in response.text for text in config.get("failed_text", [])))
            elif config["failed_type"] == "header":
                results.append(any(value in response.headers.get(key, "") for key, value in config.get("failed_header", {}).items()))
        if failed_type_logic == "or":
            result =  any(results)
        else:  
            result = all(results)
    return result

def check_success(config, session):
    if "success_type" in config:
        success_type_logic = config.get("success_type_logic", "and")
        test_urls = config.get("test_urls", [])
        if not test_urls:  
            test_urls = [config.get("test_url", "")]
        results = []
        for test_url in test_urls:
            response = session.get(test_url, timeout=10)
            if config["success_type"] == "text":
                results.append(all(text in response.text for text in config.get("success_text", [])))
            elif config["success_type"] == "header":
                results.append(all(value in response.headers.get(key, "") for key, value in config.get("success_header", {}).items()))
           
        if success_type_logic == "or":
            success = any(results)
        else:  # for "and"
            success = all(results)
        return success
    return False, None

def get_region_code(config, session):
    region_code_type = config.get("region_code_type")
    region_code_script = config.get("region_code_script")
    test_urls = config.get("test_urls", [])
    region_code_url = config.get("region_code_url", "")
    region_code_default = config.get("region_code_default", "")

    if not test_urls:  
        test_urls = [config.get("test_url", "")]

    region_codes = []
    for test_url in test_urls:
        if region_code_type == "redirect_url":
            response = session.get(test_url, timeout=10, allow_redirects=False)
            redirect_url = response.headers.get("Location", "")
            if redirect_url:
                region_code = eval(region_code_script, {"redirect_url": redirect_url})
                region_codes.append(region_code)
        elif region_code_type == "url":
            response = session.get(region_code_url, timeout=10)
            region_code = eval(region_code_script, {"response": response})
            region_codes.append(region_code)
        elif region_code_type == "fixed":
            region_code = config.get("region_code")
            region_codes.append(region_code)

    region_codes = list(set(region_codes))

    if not region_codes:
        return [region_code_default]

    return region_codes




def process_failed(config):
    print(f"{config['name']}:\t\t\t\tNo")

def process_unknown(config):
    print(f"{config['name']}:\t\t\t\tUnknown")

def process_success(config, region_code):
    print(f"{config['name']}:\t\t\t\tYes")
    if region_code is not None:
        print(f"Region Code:\t\t\t\t{region_code}")


def run_tests(configs):
    if isinstance(configs, dict):
        configs = [configs]  
    for config in configs:
        with requests.Session() as session:
            failed = check_failed(config, session)
            success = check_success(config, session)
            

            if "success_type" not in config and not failed:
                success = True

            if not failed and not success:
                process_unknown(config)
            elif failed:
                process_failed(config)
            elif success:
                region_codes = get_region_code(config, session)
                process_success(config, region_codes)

config_folder = "checker"
for file_name in os.listdir(config_folder):
    if file_name.endswith(".json"):
        file_path = os.path.join(config_folder, file_name)
        with open(file_path, "r") as json_file:
            configs = json.load(json_file)
            run_tests(configs)

