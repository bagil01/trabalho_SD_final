import socket
import json

HOST = "localhost"
PORT = 6000


def conectar():
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORT))
    return cliente


def cadastrar_residuo(cliente, empresa):

    print("\n=== CADASTRO DE RESÍDUO ===")

    tipo = input("Tipo do resíduo: ")
    quantidade = input("Quantidade (kg): ")
    localizacao = input("Localização: ")

    requisicao = {
        "acao": "cadastrar",
        "empresa": empresa,
        "tipo": tipo,
        "quantidade": quantidade,
        "localizacao": localizacao
    }

    cliente.send(json.dumps(requisicao).encode())

    resposta = json.loads(cliente.recv(4096).decode())

    print("\n[RESPOSTA DO SERVIDOR]")
    print(resposta["mensagem"])


def menu():

    print("=" * 50)
    print(" BANCO DE RESÍDUOS - CLIENTE PJ ")
    print("=" * 50)

    empresa = input("Nome da empresa: ")

    cliente = conectar()

    while True:

        print("\n=== MENU ===")
        print("1 - Cadastrar resíduo")
        print("0 - Sair")

        opcao = input("Escolha: ")

        if opcao == "1":
            cadastrar_residuo(cliente, empresa)

        elif opcao == "0":
            print("Encerrando conexão...")
            cliente.close()
            break

        else:
            print("Opção inválida!")


if __name__ == "__main__":
    menu()