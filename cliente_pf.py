import socket
import threading
import json

HOST = "localhost"
PORT = 6000


# ==========================
# P2P
# ==========================

participantes_grupo = []


def iniciar_servidor_p2p(porta):

    servidor_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    servidor_p2p.bind(("0.0.0.0", porta))
    servidor_p2p.listen()

    print(f"\n[P2P] Escutando na porta {porta}")

    while True:

        conn, addr = servidor_p2p.accept()

        try:

            mensagem = conn.recv(4096).decode()

            print("\n" + "=" * 50)
            print(f"[MENSAGEM P2P] {addr}")
            print(mensagem)
            print("=" * 50)

        except:
            pass

        finally:
            conn.close()


def enviar_mensagem_peer():

    if not participantes_grupo:

        print("\nVocê ainda não participa de nenhum grupo.")
        return

    print("\n=== PARTICIPANTES ===")

    for i, participante in enumerate(participantes_grupo):

        print(
            f"{i + 1} - "
            f"{participante['nome']} "
            f"({participante['ip']}:{participante['porta']})"
        )

    try:

        escolha = int(input("\nEscolha o participante: ")) - 1

        participante = participantes_grupo[escolha]

        mensagem = input("Mensagem: ")

        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        cliente.connect(
            (
                participante["ip"],
                participante["porta"]
            )
        )

        cliente.send(mensagem.encode())

        cliente.close()

        print("Mensagem enviada.")

    except Exception as erro:

        print(f"Erro: {erro}")


# ==========================
# SERVIDOR PRINCIPAL
# ==========================

def conectar():

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    cliente.connect((HOST, PORT))

    return cliente


def listar_residuos(cliente):

    requisicao = {
        "acao": "listar"
    }

    cliente.send(json.dumps(requisicao).encode())

    resposta = json.loads(
        cliente.recv(4096).decode()
    )

    print("\n=== RESÍDUOS DISPONÍVEIS ===")

    residuos = resposta["residuos"]

    if not residuos:

        print("Nenhum resíduo cadastrado.")
        return

    for residuo in residuos:

        print(
            f"\nID: {residuo['id']}"
        )
        print(
            f"Empresa: {residuo['empresa']}"
        )
        print(
            f"Tipo: {residuo['tipo']}"
        )
        print(
            f"Quantidade: {residuo['quantidade']} kg"
        )
        print(
            f"Localização: {residuo['localizacao']}"
        )


def registrar_interesse(cliente, nome, ip, porta_p2p):

    global participantes_grupo

    try:
        id_residuo = int(input("ID do resíduo: "))
        quantidade = int(input("Quantidade desejada (kg): "))

        requisicao = {
            "acao": "interesse",
            "id_residuo": id_residuo,
            "nome": nome,
            "ip": ip,
            "porta": porta_p2p,
            "quantidade": quantidade
        }

        cliente.send(json.dumps(requisicao).encode())

        resposta = json.loads(cliente.recv(4096).decode())

        if resposta["status"] == "coleta_confirmada":

            print("\n" + "=" * 50)
            print("COLETA CONFIRMADA")
            print("=" * 50)
            print(resposta["mensagem"])
            print(f"Resíduo: {resposta['residuo']['tipo']}")
            print(f"Quantidade coletada: {resposta['participante']['quantidade']} kg")
            print("Esse resíduo agora não aparecerá mais na listagem.")

        elif resposta["status"] == "aguardando":

            print("\n=== GRUPO EM FORMAÇÃO ===")
            print(resposta["mensagem"])
            print(f"Tipo: {resposta['tipo']}")
            print(f"Solicitado: {resposta['solicitado']} kg")
            print(f"Necessário: {resposta['necessario']} kg")

        elif resposta["status"] == "grupo_formado":

            participantes_grupo = []

            print("\n" + "=" * 50)
            print("GRUPO FORMADO")
            print("=" * 50)
            print(resposta["mensagem"])

            for participante in resposta["participantes"]:
                print(f"{participante['nome']} - {participante['quantidade']} kg")

                if participante["nome"] != nome:
                    participantes_grupo.append(participante)

            print("\nAgora vocês podem se comunicar via P2P.")

        else:
            print(resposta.get("mensagem", "Erro desconhecido."))

    except Exception as erro:
        print(f"Erro: {erro}")

# ==========================
# MENU
# ==========================

def menu():

    print("=" * 60)
    print(" CLIENTE PF ")
    print("=" * 60)

    nome = input("Nome: ")

    porta_p2p = int(
        input(
            "Porta P2P "
            "(7001,7002,7003...): "
        )
    )

    ip = "127.0.0.1"

    thread_p2p = threading.Thread(
        target=iniciar_servidor_p2p,
        args=(porta_p2p,),
        daemon=True
    )

    thread_p2p.start()

    cliente = conectar()

    while True:

        print("\n=== MENU PF ===")
        print("1 - Listar resíduos")
        print("2 - Registrar interesse")
        print("3 - Enviar mensagem P2P")
        print("0 - Sair")

        opcao = input("Escolha: ")

        if opcao == "1":

            listar_residuos(cliente)

        elif opcao == "2":

            registrar_interesse(
                cliente,
                nome,
                ip,
                porta_p2p
            )

        elif opcao == "3":

            enviar_mensagem_peer()

        elif opcao == "0":

            cliente.close()

            break

        else:

            print("Opção inválida.")


    if __name__ == "__main__":
        menu()