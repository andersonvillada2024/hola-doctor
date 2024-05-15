const menu = document.querySelector(".menu");
const openMenuBtn = document.querySelector(".open-menu");
const closeMenuBtn = document.querySelector(".close-menu");

function toggleMenu() {
  menu.classList.toggle("menu_opened");
}

openMenuBtn.addEventListener("click", toggleMenu);
closeMenuBtn.addEventListener("click", toggleMenu);

const menuLinks = document.querySelectorAll('.menu a[href^="#"]');

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      const id = entry.target.getAttribute("id");
      const menuLink = document.querySelector(`.menu a[href="#${id}"]`);

      if (entry.isIntersecting) {
        document.querySelector(".menu a.selected").classList.remove("selected");
        menuLink.classList.add("selected");
      }
    });
  },
  { rootMargin: "-30% 0px -70% 0px" }
);

menuLinks.forEach((menuLink) => {
  menuLink.addEventListener("click", function () {
    menu.classList.remove("menu_opened");
  });

  const hash = menuLink.getAttribute("href");
  const target = document.querySelector(hash);
  if (target) {
    observer.observe(target);
  }
});

// registro de activos
document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.getElementById('formulario');
  const inputs = document.querySelectorAll('#formulario input');

  const expresiones = {
      nombres_completos: /^[a-zA-Z\s]+$/, // Letras y espacios, pueden llevar acentos.
      cedula: /^[a-zA-Z0-9\s]+$/, // Letras, números y espacios.
      cargo: /^[a-zA-Z\s]+$/, // Letras y espacios, pueden llevar acentos.
      numero_puesto: /^\d+$/, // Solo números.
      extension: /^\d+$/, // Solo números.
      ml_pc: /^\d+$/, // Solo números.
      ml_pantalla: /^\d+$/, // Solo números.
      observaciones: /^[a-zA-Z0-9\s]+$/ // Letras, números y espacios.
  };

  const campos = {
      nombres_completos: false,
      cedula: false,
      cargo: false,
      numero_puesto: false,
      extension: false,
      ml_pc: false,
      ml_pantalla: false,
      observaciones: false
  };

  const validarFormulario = (e) => {
      const campo = e.target.name;
      const expresion = expresiones[campo];
      const input = e.target;
      const error = document.querySelector(`#grupo__${campo} .formulario__input-error`);

      if (expresion.test(input.value)) {
          document.getElementById(`grupo__${campo}`).classList.remove('formulario__grupo-incorrecto');
          document.getElementById(`grupo__${campo}`).classList.add('formulario__grupo-correcto');
          error.classList.remove('formulario__input-error-activo');
          campos[campo] = true;
      } else {
          document.getElementById(`grupo__${campo}`).classList.add('formulario__grupo-incorrecto');
          document.getElementById(`grupo__${campo}`).classList.remove('formulario__grupo-correcto');
          error.classList.add('formulario__input-error-activo');
          campos[campo] = false;
      }
  };

  inputs.forEach((input) => {
      input.addEventListener('keyup', validarFormulario);
      input.addEventListener('blur', validarFormulario);
  });

  formulario.addEventListener('submit', (e) => {
      e.preventDefault();

      const chekin = document.getElementById('terminos');
      if (Object.values(campos).every(campo => campo) && terminos.checked) {
          formulario.reset();

          document.getElementById('formulario__mensaje-exito').classList.add('formulario__mensaje-exito-activo');
          setTimeout(() => {
              document.getElementById('formulario__mensaje-exito').classList.remove('formulario__mensaje-exito-activo');
          }, 5000);

          document.querySelectorAll('.formulario__grupo-correcto').forEach((icono) => {
              icono.classList.remove('formulario__grupo-correcto');
          });
      } else {
          document.getElementById('formulario__mensaje').classList.add('formulario__mensaje-activo');
      }
  });
});
function redirectToHome() {
  window.location.href = '/';
}
// #imagen de alerta

document.addEventListener('DOMContentLoaded', function() {
  var cerrarAlerta = document.getElementById('cerrarAlerta');
  cerrarAlerta.addEventListener('click', function() {
      document.getElementById('alerta').style.right = '-100px'; // Mueve la alerta fuera de la pantalla
  });
});

// alerta
document.getElementById('formulario').addEventListener('submit', function() {
  alert('El formulario se ha enviado correctamente.');
});

document.addEventListener('DOMContentLoaded', function() {
  // Obtén los elementos del DOM
  var btnMedicos = document.getElementById('btnMedicos');
  var btnAdministrativos = document.getElementById('btnAdministrativos');
  var modal = document.querySelector('.modal');

  // Función para cerrar el modal
  function cerrarModal() {
      modal.classList.remove('modal--show');
  }

  // Evento de clic en el botón de médicos
  btnMedicos.addEventListener('click', function(event) {
      // Previene la acción predeterminada del enlace
      event.preventDefault();
      // Redirige a index.html
      window.location.href = '/index';
  });

  // Evento de clic en el botón de administrativos
  btnAdministrativos.addEventListener('click', function(event) {
      // Previene la acción predeterminada del enlace
      event.preventDefault();
      // Cierra el modal
      cerrarModal();
  });
});
