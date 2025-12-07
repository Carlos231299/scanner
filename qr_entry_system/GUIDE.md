# 📘 Guía de Usuario: Sistema de Acceso QR

¡Bienvenido! Este documento te enseñará a usar tu nuevo sistema paso a paso.

---

## 🚀 Inicio Rápido

1.  **Abre el sistema**: Ve a [http://localhost:5000](http://localhost:5000).
    > Verás dos botones: **"Iniciar Sesión"** y **"Escanear QR"**.

2.  **Primer Paso**: Necesitas entrar como Administrador.
    -   Haz clic en **"Iniciar Sesión"**.
    -   Usuario: `admin`
    -   Contraseña: `admin` *(o la que hayas configurado)*.

---

## 🖥️ Panel de Control (Dashboard)

Una vez dentro, verás el **Panel de Administración**. Desde aquí controlas todo.

### 1. Registrar Empleados
Para que alguien pueda entrar, primero debes registrarlo:
1.  Busca la tarjeta **"Registrar Nuevo Usuario"**.
2.  Escribe un **Nombre de Usuario** (ej. `juan.perez`).
3.  Escribe una **Contraseña**.
4.  Elige el Rol: **Empleado**.
5.  Haz clic en **Registrar**.
    > ✅ **¡Listo!** El sistema ha creado internamente el código QR para Juan.

### 2. Ver Registros (Quién entró y salió)
En la parte inferior verás una tabla llamada **"Usuarios Recientes"**.
-   Aquí aparecerá **en tiempo real** cada vez que alguien escanee su código.
-   Verás colores:
    -   🟢 **Entrada**: Verde
    -   🔴 **Salida**: Rojo
    -   🟡 **Almuerzo**: Amarillo/Azul

---

## 📷 Cómo Escanear Códigos QR

Para registrar una entrada o salida:

1.  En el Dashboard, haz clic en el botón grande **"Abrir Escáner QR"**.
2.  Si el navegador te pide permiso para usar la cámara, dile que **SÍ**.
3.  **Selecciona la Acción**: Antes de escanear, elige qué vas a hacer en el menú desplegable:
    -   ¿Va a entrar? -> Elige **Entrada**.
    -   ¿Se va a comer? -> Elige **Inicio Almuerzo**.
    -   ¿Se va a casa? -> Elige **Salida**.
4.  **Muestra el QR**: Pon el código QR del empleado frente a la cámara.
5.  Escucharás un *beep* (o verás un mensaje verde) confirmando el registro.

---

## 🛠️ Preguntas Frecuentes

**Q: ¿Dónde consigo el código QR del empleado?**
*R: Por ahora, el sistema genera el código internamente. En una futura mejora, podemos agregar un botón para "Imprimir QR". Mientras tanto, puedes usar la API `/generate_qr_image` si sabes usarla, o pedirme que agregue un botón de "Ver QR" en el panel.*

**Q: Los botones de inicio no hacían nada.**
*R: ¡Ya está arreglado! Ahora al hacer clic te llevarán a la página correcta.*

**Q: ¿Cómo lo apago?**
*R: Si usas Docker, cierra la terminal o dale al botón "Stop" en Docker Desktop.*

---

## 📱 Acceso desde el Móvil o Tablet

Si quieres usar el sistema desde tu celular (estando conectado al mismo WiFi):

1.  Averigua la **IP de tu PC**.
    - Abre una terminal (CMD) y escribe `ipconfig`.
    - Busca donde diga `IPv4 Address` (ej. `192.168.1.15`).
2.  En el navegador de tu celular, escribe esa IP y el puerto 5000.
    -   **IMPORTANTE**: Ahora debes usar `https://`.
    -   Ejemplo: `https://192.168.1.15:5000`
3.  **Advertencia de Seguridad**:
    -   El navegador te mostrará una pantalla roja de "La conexión no es privada".
    -   Esto es normal (porque usamos un certificado de desarrollo).
    -   Pulsa en **"Configuración Avanzada"** -> **"Continuar a... (inseguro)"**.
4.  ¡Listo! Ahora el navegador te permitirá usar la cámara.

---

## ❓ Solución de Problemas

**No carga en el celular:**
1.  **Firewall de Windows**: Es la causa #1.
    -   Cuando iniciaste `python` o `Docker`, Windows debió preguntarte si permitías el acceso.
    -   Si le diste a "Cancelar" o cerraste la ventana, está bloqueado.
    -   **Solución**: Escribe "Firewall" en el inicio de Windows -> "Permitir una aplicación..." -> Busca `python.exe` o `Docker` y marca las casillas "Privada" y "Pública".
2.  **Reiniciar**: Si cambiaste la configuración, asegúrate de **detener** el servidor (Ctrl+C en la terminal) y **volver a iniciarlo** para que tome el cambio de red.
