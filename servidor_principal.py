import socket
import threading
import json

HOST = "0.0.0.0"
PORT = 6000

clientes = []
residuos = []
grupos = {}

proximo_id_residuo = 1

lock = threading.Lock()


def enviar(cliente, mensagem):
    try:
        cliente.send(json.dumps(mensagem).encode())
    except:
        pass


def broadcast(mensagem):
    for cliente in clientes:
        enviar(cliente, mensagem)


def cadastrar_residuo(dados):
    global proximo_id_residuo

    with lock:

        dados["id"] = proximo_id_residuo

        residuos.append(dados)

        grupos[proximo_id_residuo] = {
            "id_residuo": proximo_id_residuo,
            "tipo": dados["tipo"],
            "quantidade_disponivel": int(dados["quantidade"]),
            "quantidade_solicitada": 0,
            "participantes": []
        }

        proximo_id_residuo += 1

        return dados["id"]


def listar_residuos():
    with lock:
        return residuos.copy()


def registrar_interesse(requisicao):

    id_residuo = requisicao["id_residuo"]

    with lock:

        if id_residuo not in grupos:
            return {
                "status": "erro",
                "mensagem": "Resíduo não encontrado."
            }

        grupo = grupos[id_residuo]

        participante = {
            "nome": requisicao["nome"],
            "ip": requisicao["ip"],
            "porta": requisicao["porta"],
            "quantidade": int(requisicao["quantidade"])
        }

        grupo["participantes"].append(participante)

        grupo["quantidade_solicitada"] += participante["quantidade"]

        if grupo["quantidade_solicitada"] >= grupo["quantidade_disponivel"]:

            return {
                "status": "grupo_formado",
                "tipo": grupo["tipo"],
                "participantes": grupo["participantes"]
            }

        return {
            "status": "aguardando",
            "tipo": grupo["tipo"],
            "solicitado": grupo["quantidade_solicitada"],
            "necessario": grupo["quantidade_disponivel"]
        }


def tratar_cliente(conn, addr):

    print(f"[NOVA CONEXÃO] {addr}")

    clientes.append(conn)

    try:

        while True:

            dados = conn.recv(4096)

            if not dados:
                break

            requisicao = json.loads(dados.decode())

            acao = requisicao.get("acao")

            # ==========================
            # CADASTRAR RESÍDUO (PJ)
            # ==========================
            if acao == "cadastrar":

                residuo = {
                    "empresa": requisicao["empresa"],
                    "tipo": requisicao["tipo"],
                    "quantidade": requisicao["quantidade"],
                    "localizacao": requisicao["localizacao"]
                }

                id_residuo = cadastrar_residuo(residuo)

                resposta = {
                    "status": "sucesso",
                    "mensagem": "Resíduo cadastrado com sucesso!",
                    "id_residuo": id_residuo
                }

                enviar(conn, resposta)

                broadcast({
                    "status": "novo_residuo",
                    "mensagem": f"Novo resíduo cadastrado: {residuo['tipo']}"
                })

                print(f"\n[NOVO RESÍDUO]")
                print(residuo)

            # ==========================
            # LISTAR RESÍDUOS (PF)
            # ==========================
            elif acao == "listar":

                resposta = {
                    "status": "lista",
                    "residuos": listar_residuos()
                }

                enviar(conn, resposta)

            # ==========================
            # REGISTRAR INTERESSE
            # ==========================
            elif acao == "interesse":

                resposta = registrar_interesse(requisicao)

                enviar(conn, resposta)

                if resposta["status"] == "grupo_formado":

                    print("\n[GRUPO FORMADO]")
                    print(f"Resíduo: {resposta['tipo']}")

                    for participante in resposta["participantes"]:

                        print(
                            f"{participante['nome']} -> "
                            f"{participante['quantidade']}kg"
                        )

            # ==========================
            # VISUALIZAR GRUPO
            # ==========================
            elif acao == "ver_grupo":

                id_residuo = requisicao["id_residuo"]

                if id_residuo in grupos:

                    enviar(conn, {
                        "status": "grupo",
                        "grupo": grupos[id_residuo]
                    })

                else:

                    enviar(conn, {
                        "status": "erro",
                        "mensagem": "Grupo não encontrado."
                    })

            # ==========================
            # AÇÃO INVÁLIDA
            # ==========================
            else:

                enviar(conn, {
                    "status": "erro",
                    "mensagem": "Ação inválida."
                })

    except Exception as erro:

        print(f"[ERRO] {erro}")

    finally:

        if conn in clientes:
            clientes.remove(conn)

        conn.close()

        print(f"[DESCONECTADO] {addr}")


def iniciar_servidor():

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    servidor.bind((HOST, PORT))
    servidor.listen()

    print("=" * 60)
    print(" SERVIDOR - BANCO DE RESÍDUOS DISTRIBUÍDO ")
    print("=" * 60)
    print(f"Rodando em {HOST}:{PORT}")
    print("Aguardando conexões...\n")

    while True:

        conn, addr = servidor.accept()

        thread = threading.Thread(
            target=tratar_cliente,
            args=(conn, addr)
        )

        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    iniciar_servidor()