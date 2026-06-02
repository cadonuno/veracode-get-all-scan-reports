from veracode_api_py import Applications, XMLAPI
import argparse
import os
import time
import xml.etree.ElementTree as ET

MAX_ATTEMPTS = 10
IS_TEST = True

def xml_to_json(element):
    data = {}
    if element.attrib:
        data.update(element.attrib)

    children = list(element)
    if children:
        for child in children:
            child_value = xml_to_json(child)
            if child.tag in data:
                if isinstance(data[child.tag], list):
                    data[child.tag].append(child_value)
                else:
                    data[child.tag] = [data[child.tag], child_value]
            else:
                data[child.tag] = child_value

    text = element.text.strip() if element.text and element.text.strip() else None
    if text:
        if data:
            data["text"] = text
        else:
            return text

    return data

def parse_xml(xml_data):
    try:
        root = ET.fromstring(xml_data)

        return [xml_to_json(child) for child in root]
    except ET.ParseError as e:
        print(f"Failed to parse XML data - {e}")
        return None

def try_get_all_applications(attempt=1):
    try:
        return Applications().get_all()
    except Exception as e:
        print(f"Attempt {attempt}: Failed to get applications - {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 ** attempt)
            return try_get_all_applications(attempt + 1)
        else:
            print("Exceeded maximum retry attempts. Exiting.")
            return []

def try_get_report(build_id, file_format, attempt=1):
    try:
        return XMLAPI().get_detailed_report(build_id) if file_format == "xml" else XMLAPI().get_detailed_report_pdf(build_id)
    except Exception as e:
        print(f"Attempt {attempt}: Failed to get report for build {build_id} - {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 ** attempt)
            return try_get_report(build_id, file_format, attempt + 1)
        else:
            print(f"Exceeded maximum retry attempts for build {build_id}. Skipping.")
            return None

def try_get_all_scans(app_id, attempt=1):
    try:
        raw = XMLAPI().get_build_list(app_id)
        return parse_xml(raw)
    except Exception as e:
        print(f"Attempt {attempt}: Failed to get scans for app {app_id} - {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 ** attempt)
            return try_get_all_scans(app_id, attempt + 1)
        else:
            print(f"Exceeded maximum retry attempts for app {app_id}. Skipping.")
            return []

def try_get_all_sandbox_scans(app_id, sandbox_id, attempt=1):
    try:
        raw = XMLAPI().get_build_list(app_id, sandbox_id)
        return parse_xml(raw)
    except Exception as e:
        print(f"Attempt {attempt}: Failed to get sandbox scans for app {app_id} - {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 ** attempt)
            return try_get_all_sandbox_scans(app_id, sandbox_id, attempt + 1)
        else:
            print(f"Exceeded maximum retry attempts for app {app_id}. Skipping.")
            return []

def save_reports_from_build_list(build_list, base_directory, file_format):
    for build in build_list:
        report = try_get_report(build["build_id"], file_format)
        if report:
            file_name = os.path.join(base_directory, f"scan_report_{build['version']}.{file_format}")
            with open(file_name, "wb") as file:
                file.write(report)

def try_get_sandbox_list(app_id, attempt=1):
    try:
        raw = XMLAPI().get_sandbox_list(app_id)
        return parse_xml(raw)
    except Exception as e:
        print(f"Attempt {attempt}: Failed to get sandbox list for app {app_id} - {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(2 ** attempt)
            return try_get_sandbox_list(app_id, attempt + 1)
        else:
            print(f"Exceeded maximum retry attempts for app {app_id}. Skipping.")
            return []

def main():

    if IS_TEST:
        out_dir = os.path.abspath("test_reports")
        file_format = "pdf"
    else:
        parser = argparse.ArgumentParser(description="Download Veracode reports for all applications")
        parser.add_argument("--output", "-o", required=True, help="Folder to save all reports")
        parser.add_argument("--format", "-f", choices=["pdf", "xml"], default="pdf", help="Report format to save (pdf or xml)")
        args = parser.parse_args()

        out_dir = os.path.abspath(args.output)
        file_format = args.format
    os.makedirs(out_dir, exist_ok=True)

    # Get all applications
    applications = try_get_all_applications()

    # For each application, save a placeholder report file in the chosen format
    for app in applications:
        base_directory = os.path.join(out_dir, app["profile"]["name"].replace(" ", "_").replace("/", "_"))
        os.makedirs(base_directory, exist_ok=True) # Sanitize name for filename
        save_reports_from_build_list(try_get_all_scans(app["id"]), base_directory, file_format)
        sandbox_list = try_get_sandbox_list(app["id"])
        for sandbox in sandbox_list:
            sandbox_directory = os.path.join(base_directory, f"sandbox_{sandbox['sandbox_name']}".replace(" ", "_").replace("/", "_"))
            os.makedirs(sandbox_directory, exist_ok=True)
            save_reports_from_build_list(try_get_all_sandbox_scans(app["id"], sandbox["sandbox_id"]), sandbox_directory, file_format)

        
        


if __name__ == "__main__":
    main()