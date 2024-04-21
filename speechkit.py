import logging
import requests


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)


def create_iam_token():
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(url=metadata_url, headers=headers)
    logging.info("Создан новый iam_token")
    return response.json()


def speech_to_text(data, iam_token, folder_id):
    params = "&".join([
        "topic=general",
        f"folderId={folder_id}",
        "lang=ru-RU"
    ])

    headers = {
        'Authorization': f'Bearer {iam_token}',
    }

    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        logging.info('success stt')
        return decoded_data.get("result")
    else:
        logging.error(f"При запросе в SpeechKit возникла ошибка {decoded_data.get("error_code")}")
        return False
