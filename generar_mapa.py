import ast
import os
from pyvis.network import Network

# Crear la red con fondo oscuro y texto claro
net = Network(
    height="800px",
    width="100%",
    bgcolor="#1e1e1e",
    font_color="white",
    directed=True,
)

py_files = {}

# 1. Registrar archivos del proyecto
for root, _, files in os.walk("."):
    if any(
        x in root for x in ["venv", ".git", "__pycache__", ".devcontainer"]
    ):
        continue
    for file in files:
        if file.endswith(".py") and file != "generar_mapa.py":
            rel_path = os.path.relpath(os.path.join(root, file))
            # Crear identificador de módulo (ej: views.tab_1_perfil)
            mod_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
            py_files[mod_name] = rel_path

            # Agregar nodo con etiqueta visible
            net.add_node(
                rel_path,
                label=file,
                title=f"Ruta: {rel_path}",
                shape="box",
                color="#4A90E2",
            )

# 2. Leer importaciones y trazar las líneas de conexión
for mod_name, filepath in py_files.items():
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)

        for node in ast.walk(tree):
            imported_mod = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_mod = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_mod = node.module

            if imported_mod:
                for target_mod, target_path in py_files.items():
                    # Si un archivo importa a otro del proyecto, crear conexión
                    if target_mod in imported_mod and filepath != target_path:
                        net.add_edge(
                            filepath,
                            target_path,
                            color="#888888",
                            arrows="to",
                        )
    except Exception:
        pass

# Desactivar física excesiva para que no vuelen los nodos
net.toggle_physics(True)
net.write_html("mapa_interactivo.html")
print("¡Mapa con conexiones generado exitosamente!")