/* intake-conditional.js — Conditional field logic for intake forms */

document.addEventListener('DOMContentLoaded', function () {

  // ── CPF mask ──────────────────────────────────────────────────────────────
  var cpfInput = document.getElementById('cpf');
  if (cpfInput) {
    cpfInput.addEventListener('input', function () {
      var v = this.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 9) {
        v = v.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2}).*/, '$1.$2.$3-$4');
      } else if (v.length > 6) {
        v = v.replace(/^(\d{3})(\d{3})(\d{0,3}).*/, '$1.$2.$3');
      } else if (v.length > 3) {
        v = v.replace(/^(\d{3})(\d{0,3}).*/, '$1.$2');
      }
      this.value = v;
    });
  }

  // ── Policial Militar checkbox ─────────────────────────────────────────────
  var pmCheckbox = document.getElementById('policial_militar');
  var pmFields   = document.getElementById('pm-fields-container');
  var pmVitimas  = document.getElementById('pm-vitimas-container');

  function togglePmFields() {
    if (!pmCheckbox) return;
    var checked = pmCheckbox.checked;

    if (pmFields) {
      pmFields.style.display = checked ? 'block' : 'none';
      if (!checked) {
        pmFields.querySelectorAll('input').forEach(function (i) { i.value = ''; });
      }
    }

    if (pmVitimas) {
      pmVitimas.style.display = checked ? 'block' : 'none';
    }
  }

  if (pmCheckbox) {
    pmCheckbox.addEventListener('change', togglePmFields);
    togglePmFields(); // Preserve state on page load (e.g. after validation error)
  }

  // ── Vítimas (PM) — add / remove ──────────────────────────────────────────
  var usedIndices = new Set();
  var MAX_VITIMAS = 5;

  function updateVitimaCount() {
    var container = document.getElementById('vitimas-list');
    var counter = document.getElementById('vitima-counter');
    if (!container || !counter) return;
    var active = container.querySelectorAll('.vitima-block:not(.removed)').length;
    counter.textContent = active + '/' + MAX_VITIMAS;
  }

  window.addVitima = function () {
    var container = document.getElementById('vitimas-list');
    if (!container) return;

    var active = container.querySelectorAll('.vitima-block:not(.removed)');
    if (active.length >= MAX_VITIMAS) return;

    // Find the lowest available slot index (1–5)
    var idx = 1;
    while (idx <= MAX_VITIMAS && usedIndices.has(idx)) idx++;
    if (idx > MAX_VITIMAS) return;

    usedIndices.add(idx);

    var card = document.createElement('div');
    card.className = 'card mb-2 vitima-block';
    card.dataset.index = idx;
    card.innerHTML =
      '<div class="card-body py-2">' +
        '<div class="d-flex justify-content-between align-items-center mb-2">' +
          '<strong class="small">Vítima ' + idx + '</strong>' +
          '<button type="button" class="btn btn-outline-danger btn-sm" onclick="removeVitima(this)">Remover</button>' +
        '</div>' +
        '<div class="row">' +
          '<div class="col-md-6 mb-2">' +
            '<label class="form-label small mb-1">Nome</label>' +
            '<input type="text" class="form-control form-control-sm" name="vitima__' + idx + '__nome" maxlength="200" autocomplete="off">' +
          '</div>' +
          '<div class="col-md-3 mb-2">' +
            '<label class="form-label small mb-1">Data de Nascimento</label>' +
            '<input type="date" class="form-control form-control-sm" name="vitima__' + idx + '__data_nascimento" autocomplete="off">' +
          '</div>' +
          '<div class="col-md-4 mb-2">' +
            '<label class="form-label small mb-1">RG</label>' +
            '<input type="text" class="form-control form-control-sm" name="vitima__' + idx + '__rg" maxlength="20" autocomplete="off">' +
          '</div>' +
          '<div class="col-md-4 mb-2">' +
            '<label class="form-label small mb-1">CPF</label>' +
            '<input type="text" class="form-control form-control-sm vitima-cpf" name="vitima__' + idx + '__cpf" maxlength="14" placeholder="000.000.000-00" autocomplete="off" inputmode="numeric">' +
          '</div>' +
          '<div class="col-md-4 mb-2">' +
            '<label class="form-label small mb-1">E-mail</label>' +
            '<input type="email" class="form-control form-control-sm" name="vitima__' + idx + '__email" maxlength="200" autocomplete="off">' +
          '</div>' +
          '<div class="col-12 mb-2">' +
            '<label class="form-label small mb-1">Endereço</label>' +
            '<input type="text" class="form-control form-control-sm" name="vitima__' + idx + '__endereco" maxlength="400" autocomplete="off">' +
          '</div>' +
        '</div>' +
      '</div>';
    container.appendChild(card);

    var cpfField = card.querySelector('.vitima-cpf');
    if (cpfField) {
      cpfField.addEventListener('input', function () {
        var v = this.value.replace(/\D/g, '').slice(0, 11);
        if (v.length > 9) {
          v = v.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2}).*/, '$1.$2.$3-$4');
        } else if (v.length > 6) {
          v = v.replace(/^(\d{3})(\d{3})(\d{0,3}).*/, '$1.$2.$3');
        } else if (v.length > 3) {
          v = v.replace(/^(\d{3})(\d{0,3}).*/, '$1.$2');
        }
        this.value = v;
      });
    }

    updateVitimaCount();
  };

  window.removeVitima = function (btn) {
    var card = btn.closest('.vitima-block');
    if (!card) return;
    var idx = parseInt(card.dataset.index, 10);
    // Clear all inputs so removed victim data is not submitted
    card.querySelectorAll('input').forEach(function (i) { i.value = ''; });
    card.classList.add('removed');
    card.style.display = 'none';
    usedIndices.delete(idx);
    updateVitimaCount();
  };

  // ── Roubo/Furto — relato livre condicional ───────────────────────────────
  var tipoOcorrencia = document.getElementById('tipo_ocorrencia_rf');
  var relatoContainer = document.getElementById('relato-rf-container');

  function toggleRelatoRF() {
    if (!tipoOcorrencia || !relatoContainer) return;
    relatoContainer.style.display = tipoOcorrencia.value ? 'block' : 'none';
  }

  if (tipoOcorrencia) {
    tipoOcorrencia.addEventListener('change', toggleRelatoRF);
    toggleRelatoRF(); // Preserve on reload
  }

  // ── Violência Doméstica — botão questionários ─────────────────────────────
  var possuiMP   = document.querySelector('[name="q_medida_protetiva"]');
  var desejaMP   = document.querySelector('[name="q_deseja_medida_protetiva"]');
  var btnQuest   = document.getElementById('btn-questionarios-vd');

  function toggleBtnQuestionarios() {
    if (!btnQuest) return;
    var naoTemMP  = possuiMP  && possuiMP.value  === 'nao';
    var desejaQ   = desejaMP  && desejaMP.value  === 'sim';
    btnQuest.style.display = (naoTemMP && desejaQ) ? 'block' : 'none';
  }

  if (possuiMP)  possuiMP.addEventListener('change',  toggleBtnQuestionarios);
  if (desejaMP)  desejaMP.addEventListener('change',  toggleBtnQuestionarios);
  toggleBtnQuestionarios();

  // ── Photo / PDF upload validation (max 3 files) ──────────────────────────
  var photoInput = document.getElementById('photos-input');
  var photoFeedback = document.getElementById('photos-feedback');

  if (photoInput) {
    photoInput.addEventListener('change', function () {
      var MAX_FILES = 3;
      var ALLOWED   = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
      var files     = Array.from(this.files);
      var errors    = [];

      if (files.length > MAX_FILES) {
        errors.push('Máximo de ' + MAX_FILES + ' arquivos permitidos.');
        this.value = '';
      } else {
        files.forEach(function (f) {
          if (!ALLOWED.includes(f.type)) {
            errors.push('"' + f.name + '" não é um formato aceito (JPEG, PNG, GIF, PDF).');
          }
        });
        if (errors.length) this.value = '';
      }

      if (photoFeedback) {
        photoFeedback.textContent = errors.join(' ');
        photoFeedback.style.display = errors.length ? 'block' : 'none';
      }
    });
  }

});
