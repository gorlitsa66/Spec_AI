from gigachat import GigaChat
import ssl


def gpt_request(text):
    ssl_c = ssl.create_default_context()
    ssl_c.check_hostname = False
    ssl_c.verify_mode = ssl.CERT_NONE
    giga = GigaChat(
        credentials=open('gpt_api.txt').read(),
        scope='GIGACHAT_API_PERS',
        model='Gigachat',
        verify_ssl_certs=False
    )

    answer = giga.chat(text)
    return (answer.choices[0].message.content)


if __name__ == '__main__':
    print('TEST')
    print(gpt_request("Придумай стих про поросят"))
