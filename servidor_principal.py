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
        dados["disponivel"] = True

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
        return [
            residuo for residuo in residuos
            if residuo.get("disponivel", True)
        ]


def buscar_residuo_por_id(id_residuo):
    for residuo in residuos:
        if residuo["id"] == id_residuo:
            return residuo
    return None


def registrar_interesse(requisicao):
    id_residuo = int(requisicao["id_residuo"])
    quantidade_desejada = int(requisicao["quantidade"])

    with lock:
        residuo = buscar_residuo_por_id(id_residuo)

        if residuo is None:
            return {
                "status": "erro",
                "mensagem": "Resíduo não encontrado."
            }

        if not residuo.get("disponivel", True):
            return {
                "status": "erro",
                "mensagem": "Este resíduo já está indisponível."
            }

        quantidade_disponivel = int(residuo["quantidade"])

        if quantidade_desejada <= 0:
            return {
                "status": "erro",
                "mensagem": "A quantidade deve ser maior que zero."
            }

        if quantidade_desejada > quantidade_disponivel:
            return {
                "status": "erro",
                "mensagem": "Quantidade solicitada maior que a disponível."
            }

        participante = {
            "nome": requisicao["nome"],
            "ip": requisicao["ip"],
            "porta": requisicao["porta"],
            "quantidade": quantidade_desejada
        }

        if quantidade_desejada == quantidade_disponivel:
            residuo["disponivel"] = False

            return {
                "status": "coleta_confirmada",
                "mensagem": "Coleta confirmada! O resíduo agora está indisponível.",
                "residuo": residuo,
                "participante": participante
            }

        grupo = grupos[id_residuo]

        grupo["participantes"].append(participante)
        grupo["quantidade_solicitada"] += quantidade_desejada

        if grupo["quantidade_solicitada"] >= quantidade_disponivel:
            residuo["disponivel"] = False

            return {
                "status": "grupo_formado",
                "mensagem": "Grupo formado! O resíduo agora está indisponível.",
                "tipo": grupo["tipo"],
                "participantes": grupo["participantes"]
            }

        return {
            "status": "aguardando",
            "mensagem": "Interesse registrado. Aguardando mais participantes.",
            "tipo": grupo["tipo"],
            "solicitado": grupo["quantidade_solicitada"],
            "necessario": quantidade_disponivel
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

                print("\n[NOVO RESÍDUO]")
                print(residuo)

            elif acao == "listar":
                resposta = {
                    "status": "lista",
                    "residuos": listar_residuos()
                }

                enviar(conn, resposta)

            elif acao == "interesse":
                resposta = registrar_interesse(requisicao)
                enviar(conn, resposta)

                if resposta["status"] == "coleta_confirmada":
                    print("\n[COLETA CONFIRMADA]")
                    print(f"Resíduo: {resposta['residuo']['tipo']}")
                    print(f"Coletor: {resposta['participante']['nome']}")
                    print(f"Quantidade: {resposta['participante']['quantidade']}kg")

                elif resposta["status"] == "grupo_formado":
                    print("\n[GRUPO FORMADO]")
                    print(f"Resíduo: {resposta['tipo']}")

                    for participante in resposta["participantes"]:
                        print(
                            f"{participante['nome']} -> "
                            f"{participante['quantidade']}kg"
                        )

            elif acao == "ver_grupo":
                id_residuo = int(requisicao["id_residuo"])

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