document.addEventListener("DOMContentLoaded", function () {
  var modalElement = document.getElementById("confirmAction");
  var titleElement = document.getElementById("confirmActionTitle");
  var messageElement = document.getElementById("confirmActionMessage");
  var submitButton = document.getElementById("confirmActionSubmit");
  var pendingForm = null;
  var confirmedForms = new WeakSet();
  var modal = modalElement && window.bootstrap
    ? window.bootstrap.Modal.getOrCreateInstance(modalElement)
    : null;

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.matches(".js-confirm-action")) {
      return;
    }
    if (confirmedForms.has(form)) {
      confirmedForms.delete(form);
      return;
    }

    event.preventDefault();
    var title = form.dataset.confirmTitle || "¿Confirmas esta acción?";
    var message = form.dataset.confirmMessage || "Esta acción no se puede deshacer.";

    if (!modal) {
      if (window.confirm(title + "\n\n" + message)) {
        confirmedForms.add(form);
        form.requestSubmit();
      }
      return;
    }

    pendingForm = form;
    titleElement.textContent = title;
    messageElement.textContent = message;
    modal.show();
  });

  if (submitButton) {
    submitButton.addEventListener("click", function () {
      if (!pendingForm) {
        return;
      }
      var form = pendingForm;
      pendingForm = null;
      modal.hide();
      confirmedForms.add(form);
      form.requestSubmit();
    });
  }
});
