const chatbotCircle = document.getElementById('chatbot-circle');
const chatbotBox = document.querySelector('.chatbot-box');
const llamaForm = document.getElementById('llamaForm');

// Evento para abrir/cerrar el cuadro de chat
chatbotCircle.addEventListener('click', () => {
    chatbotBox.classList.toggle('active'); // Alterna la clase 'active' para mostrar/ocultar el cuadro de chat
});
llamaForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const userInput = document.getElementById('userInput').value;

    if (userInput.trim() !== "") {
        console.log(`Enviando mensaje: ${userInput}`); // Agregar un log para asegurarse que el valor se está tomando correctamente

        fetch('/llama', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: userInput })
        })
        .then(response => response.json())
        .then(data => {
            const chatbotBody = document.querySelector('.chatbot-body');

            const userMessage = document.createElement('p');
            userMessage.textContent = `Tú: ${userInput}`;
            chatbotBody.appendChild(userMessage);

            const botMessage = document.createElement('p');
            botMessage.textContent = `Bot: ${data.response}`;
            chatbotBody.appendChild(botMessage);

            document.getElementById('userInput').value = '';
        })
        .catch(error => {
            console.error('Error al conectar con el backend:', error);
        });
    }
});








// Funcionalidades del resto de la aplicación

const modal = document.getElementById("modal");
const modalTarjeta = document.getElementById("modalTarjeta");
const modalEstadoCuenta = document.getElementById("modalEstadoCuenta");

const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const closeTarjetaBtn = document.getElementById("closeTarjetaBtn");
const closeEstadoCuentaBtn = document.getElementById("closeEstadoCuentaBtn");

const addTarjetaBtn = document.getElementById("addTarjetaBtn");
const addEstadoBtn = document.getElementById("addEstadoBtn");

// Abrir la primera ventana emergente
openModalBtn.onclick = function() {
    modal.style.display = "flex";
}

// Cerrar la primera ventana emergente
closeModalBtn.onclick = function() {
    modal.style.display = "none";
}

// Abrir la ventana de agregar tarjeta
addTarjetaBtn.onclick = function() {
    modal.style.display = "none";  // Cerrar la primera ventana
    modalTarjeta.style.display = "flex";  // Abrir la segunda ventana
}

// Cerrar la ventana de agregar tarjeta
closeTarjetaBtn.onclick = function() {
    modalTarjeta.style.display = "none";
}

// Abrir la ventana de subir estado de cuenta
addEstadoBtn.onclick = function() {
    modal.style.display = "none";  // Cerrar la primera ventana
    modalEstadoCuenta.style.display = "flex";  // Abrir la tercera ventana
}

// Cerrar la ventana de subir estado de cuenta
closeEstadoCuentaBtn.onclick = function() {
    modalEstadoCuenta.style.display = "none";
}

// Cerrar cualquier ventana emergente al hacer clic fuera
window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    } else if (event.target === modalTarjeta) {
        modalTarjeta.style.display = "none";
    } else if (event.target === modalEstadoCuenta) {
        modalEstadoCuenta.style.display = "none";
    }
}

// Funcionalidad de los tres puntos para mostrar el menú de opciones
const menuButtons = document.querySelectorAll('.menu-button');
menuButtons.forEach(button => {
    button.addEventListener('click', function() {
        const card = this.closest('.card');
        card.classList.toggle('active');
    });
});

// Ocultar el menú de opciones al hacer clic fuera de la tarjeta
window.onclick = function(event) {
    if (!event.target.matches('.menu-button')) {
        const menus = document.querySelectorAll('.card.active');
        menus.forEach(menu => menu.classList.remove('active'));
    }
}

// Funcionalidad de eliminar tarjeta
const deleteOptions = document.querySelectorAll('.delete-option');
deleteOptions.forEach(option => {
    option.addEventListener('click', function(event) {
        event.preventDefault();
        const cardId = this.getAttribute('data-card-id');
        fetch(`/delete_card/${cardId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                location.reload();  // Recargar la página después de eliminar
            }
        });
    });
});
