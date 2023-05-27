import requests
import json
import os

def check_failed(config, response):
    if "failed_type" in config:
        if config["failed_type"] == "text":
            return any(text in response.text for text in config.get("failed_text", []))
        elif config["failed_type"] == "header":
            return any(value in response.headers.get(key, "") for key, value in config.get("failed_header", {}).items())
    return False

def check_success(config, response):
    if "success_type" in config:
        if config["success_type"] == "text":
            success = all(text in response.text for text in config.get("success_text", []))
        elif config["success_type"] == "header":
            success = all(value in response.headers.get(key, "") for key, value in config.get("success_header", {}).items())
        
        if success:
            region_code = None
            try:
                region_code = get_region_code(config, response)
            except Exception as e:
                print(f"Error evaluating region_code_script: {e}")
            finally:
                return True, region_code

    return False, None

def get_region_code(config, response):
    region_code_type = config.get("region_code_type")
    region_code_script = config.get("region_code_script")
    region_code_url = config.get("region_code_url", "")
    test_url = config.get("test_url")

    session = requests.Session()

    if region_code_type == "redirect_url":
        response = session.get(test_url, timeout=10, allow_redirects=False)
        redirect_url = response.headers.get("Location", "")
        if redirect_url:
            region_code = eval(region_code_script, {"redirect_url": redirect_url})
            return region_code
    elif region_code_type == "url":
        response_url = session.get(region_code_url, timeout=10)
        region_code = eval(region_code_script, {"response": response_url})
        return region_code


def process_failed(config):
    print(f"{config['name']}:\t\t\t\tNo")

def process_unknown(config):
    print(f"{config['name']}:\t\t\t\tUnknown")

def process_success(config, response):
    region_code = None
    try:
        region_code = get_region_code(config, response)
    except Exception as e:
        print(f"Error evaluating region_code_script: {e}")

    print(f"{config['name']}:\t\t\t\tYes")
    if region_code is not None:
        print(f"Region Code:\t\t\t\t{region_code}")

def run_test(config):
    session = requests.Session()
    response = session.get(config["test_url"], timeout=10)

    failed = check_failed(config, response)
    success = check_success(config, response)

    if "success_type" not in config and not failed:
        success = True

    if not failed and not success:
        process_unknown(config)
    elif failed:
        process_failed(config)
    elif success:
        process_success(config, response)


config_folder = "checker"
for file_name in os.listdir(config_folder):
    if file_name.endswith(".json"):
        file_path = os.path.join(config_folder, file_name)
        with open(file_path, "r") as json_file:
            config = json.load(json_file)
            run_test(config)
