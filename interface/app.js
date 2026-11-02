/*
 * Interface web - consomme l'API REST/JSON de ce projet (voir api/ et
 * 00_analyse/05_COUCHE_API.md).
 *
 * Cette page est servie directement par le serveur FastAPI (voir
 * api/app.py, StaticFiles monte sur "/") : les appels fetch() ci-dessous
 * utilisent donc des chemins relatifs ("/entites", "/sante"...), sur la
 * MEME origine que l'API - pas besoin de configurer d'URL ni de se
 * soucier du CORS pour cette page elle-meme (le CORS reste utile pour
 * d'autres clients qui consommeraient l'API depuis une autre origine).
 */

const selecteurEntite = document.getElementById("selecteur-entite");
const selecteurOperation = document.getElementById("selecteur-operation");
const champIdentifiant = document.getElementById("champ-identifiant");
const zoneChampsDynamiques = document.getElementById("zone-champs-dynamiques");
const champPage = document.getElementById("champ-page");
const champTaillePage = document.getElementById("champ-taille-page");
const champConfirmer = document.getElementById("champ-confirmer");
const zoneIdentifiant = document.getElementById("zone-identifiant");
const zoneDonnees = document.getElementById("zone-donnees");
const zonePagination = document.getElementById("zone-pagination");
const zoneConfirmerSuppression = document.getElementById("zone-confirmer-suppression");
const zoneMessage = document.getElementById("zone-message");
const zoneResultats = document.getElementById("zone-resultats");
const boutonExecuter = document.getElementById("bouton-executer");
const statutConnexion = document.getElementById("statut-connexion");

/**
 * Objectif : afficher un message [SUCCES]/[ERREUR]/[VALIDATION] dans la
 * zone de resultat, avec la couleur correspondante.
 *
 * Parametres : type ("succes" | "erreur" | "validation"), texte (string).
 */
function afficherMessage(type, texte) {
  zoneMessage.innerHTML = `<div class="message ${type}">${texte}</div>`;
}

/**
 * Objectif : deviner le type HTTP d'erreur (ErreurValidation,
 * ErreurEntiteInconnue...) pour choisir la bonne couleur d'affichage.
 */
function classeMessagePourErreur(typeErreur) {
  if (typeErreur === "ErreurValidation" || typeErreur === "ErreurEntiteInconnue") {
    return "validation";
  }
  return "erreur";
}

/*
 * Champs de saisie generes dynamiquement pour creer()/modifier(), a
 * partir de GET /entites/{entite}/champs (crud/registre_entites.py,
 * "champs_formulaire") : un champ texte (avec suggestions, ComboBox
 * editable) ou une liste deroulante (ComboBox fermee, ex: Type de tiers),
 * selon la description renvoyee par le serveur - jamais de zone de texte
 * libre a remplir "a la main" avec des noms de champs Sage.
 */

let champsFormulaireParEntite = {};

/** Charge (une seule fois, avec mise en cache) la description des champs
 * de formulaire d'une entite (GET /entites/{entite}/champs). */
async function chargerChampsEntite(entite) {
  if (!entite || champsFormulaireParEntite[entite]) {
    return;
  }
  try {
    const reponse = await fetch(`/entites/${encodeURIComponent(entite)}/champs`);
    champsFormulaireParEntite[entite] = await reponse.json();
  } catch (erreur) {
    champsFormulaireParEntite[entite] = { champ_cle: null, champs: [] };
  }
}

/**
 * Objectif : (re)generer les champs de saisie de la zone "Données", selon
 * l'entité et l'opération actuellement choisies.
 *
 * En modification, le champ clé (ex: CT_Num) n'est pas redemandé ici : il
 * est déjà saisi dans "Identifiant" (zone-identifiant).
 */
function genererChampsDonnees() {
  const entite = selecteurEntite.value;
  const operation = selecteurOperation.value;
  zoneChampsDynamiques.innerHTML = "";

  const infos = champsFormulaireParEntite[entite];
  if (!infos || !["creer", "modifier"].includes(operation)) {
    return;
  }

  infos.champs.forEach((champ) => {
    if (operation === "modifier" && champ.nom === infos.champ_cle) {
      return;
    }

    const idChamp = `champ-dyn-${champ.nom}`;
    const obligatoire = operation === "creer" && champ.obligatoire;
    const etoile = obligatoire ? " *" : "";
    const label = document.createElement("label");

    if (champ.type === "liste") {
      const options = champ.options
        .map((option) => `<option value="${option.valeur}">${option.libelle}</option>`)
        .join("");
      label.innerHTML = `${champ.libelle}${etoile}
        <select id="${idChamp}" data-nom="${champ.nom}">${options}</select>`;
    } else {
      const idListe = `${idChamp}-suggestions`;
      const suggestions = champ.suggestions || (champ.exemple ? [champ.exemple] : []);
      const optionsListe = suggestions.map((valeur) => `<option value="${valeur}"></option>`).join("");
      label.innerHTML = `${champ.libelle}${etoile}
        <input type="text" id="${idChamp}" data-nom="${champ.nom}" list="${idListe}"
               placeholder="ex: ${champ.exemple || ""}" />
        <datalist id="${idListe}">${optionsListe}</datalist>`;
    }

    zoneChampsDynamiques.appendChild(label);
  });
}

/**
 * Objectif : lire les valeurs saisies dans les champs générés par
 * genererChampsDonnees(), pour construire l'objet "donnees" envoyé dans
 * le corps JSON de creer()/modifier().
 *
 * Un champ laissé vide est simplement omis (pas envoyé) - utile pour les
 * champs optionnels en modification. Les valeurs qui ressemblent à un
 * nombre entier (ex: "0" pour CT_Type) sont converties en nombre - Sage
 * attend CT_Type sous forme numérique (voir
 * 00_analyse/04_VERIFICATION_COM.md).
 */
function lireDonneesDuFormulaire() {
  const donnees = {};
  zoneChampsDynamiques.querySelectorAll("[data-nom]").forEach((element) => {
    const valeurBrute = element.value.trim();
    if (!valeurBrute) {
      return;
    }
    donnees[element.dataset.nom] = /^-?\d+$/.test(valeurBrute)
      ? parseInt(valeurBrute, 10)
      : valeurBrute;
  });
  return donnees;
}

/**
 * Objectif : afficher les resultats d'une operation (une liste de
 * dictionnaires pour lister(), ou un seul dictionnaire pour lire()) sous
 * forme de tableau HTML simple.
 */
function afficherResultats(donnees, infoPagination) {
  if (!donnees) {
    zoneResultats.innerHTML = "";
    return;
  }

  const lignes = Array.isArray(donnees) ? donnees : [donnees];
  if (lignes.length === 0) {
    zoneResultats.innerHTML = "<p>Aucun resultat.</p>";
    return;
  }

  const colonnes = Object.keys(lignes[0]);
  const entetes = colonnes.map((c) => `<th>${c}</th>`).join("");
  const corps = lignes
    .map((ligne) => {
      const cellules = colonnes
        .map((c) => `<td>${ligne[c] === null || ligne[c] === undefined ? "" : ligne[c]}</td>`)
        .join("");
      return `<tr>${cellules}</tr>`;
    })
    .join("");

  let html = `<table><thead><tr>${entetes}</tr></thead><tbody>${corps}</tbody></table>`;
  if (infoPagination) {
    html += `<p class="pagination-info">Page ${infoPagination.page}/${infoPagination.nombre_pages} — ${infoPagination.total} resultat(s) au total.</p>`;
  }
  zoneResultats.innerHTML = html;
}

/** Verifie que l'API est en ligne (GET /sante) et met a jour le badge. */
async function verifierConnexion() {
  try {
    const reponse = await fetch("/sante");
    if (reponse.ok) {
      statutConnexion.textContent = "API en ligne";
      statutConnexion.className = "statut ok";
    } else {
      throw new Error("reponse non OK");
    }
  } catch (erreur) {
    statutConnexion.textContent = "API inaccessible";
    statutConnexion.className = "statut erreur";
  }
}

/** Charge la liste des entites connues (GET /entites) dans le selecteur,
 * puis charge les champs de formulaire de l'entite selectionnee. */
async function chargerEntites() {
  try {
    const reponse = await fetch("/entites");
    const corps = await reponse.json();
    selecteurEntite.innerHTML = corps.entites
      .map((entite) => `<option value="${entite}">${entite}</option>`)
      .join("");
  } catch (erreur) {
    selecteurEntite.innerHTML = "<option value=''>(impossible de charger)</option>";
  }
  await chargerChampsEntite(selecteurEntite.value);
  genererChampsDonnees();
}

/**
 * Objectif : afficher/masquer les zones de saisie selon l'operation
 * choisie (une entite n'a pas besoin des memes champs pour lister() que
 * pour creer(), par exemple), et regenerer les champs dynamiques.
 */
function adapterFormulaireALOperation() {
  const operation = selecteurOperation.value;

  zoneIdentifiant.hidden = !["lire", "modifier", "supprimer"].includes(operation);
  zoneDonnees.hidden = !["creer", "modifier"].includes(operation);
  zonePagination.hidden = operation !== "lister";
  zoneConfirmerSuppression.hidden = operation !== "supprimer";

  genererChampsDonnees();
}

/**
 * Objectif : executer l'operation choisie en appelant l'endpoint REST
 * correspondant, puis afficher le resultat ou l'erreur.
 */
async function executerOperation() {
  const entite = selecteurEntite.value;
  const operation = selecteurOperation.value;
  const identifiant = champIdentifiant.value.trim();

  if (!entite) {
    afficherMessage("validation", "[VALIDATION] Choisissez une entite.");
    return;
  }

  let url = `/entites/${encodeURIComponent(entite)}`;
  let options = { method: "GET" };

  if (operation === "lister") {
    const page = champPage.value || 1;
    const taillePage = champTaillePage.value || 20;
    url += `?page=${page}&taille_page=${taillePage}`;
  } else if (operation === "lire") {
    url += `/${encodeURIComponent(identifiant)}`;
  } else if (operation === "creer") {
    options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ donnees: lireDonneesDuFormulaire() }),
    };
  } else if (operation === "modifier") {
    url += `/${encodeURIComponent(identifiant)}`;
    options = {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ donnees: lireDonneesDuFormulaire() }),
    };
  } else if (operation === "supprimer") {
    url += `/${encodeURIComponent(identifiant)}?confirmer=${champConfirmer.checked}`;
    options = { method: "DELETE" };
  }

  boutonExecuter.disabled = true;
  boutonExecuter.textContent = "Patience, appel de Sage en cours...";
  afficherMessage("", "");
  zoneResultats.innerHTML = "";

  try {
    const reponse = await fetch(url, options);
    const corps = await reponse.json();

    if (!reponse.ok) {
      afficherMessage(classeMessagePourErreur(corps.type), corps.erreur);
      return;
    }

    afficherMessage("succes", corps.message || "Operation reussie.");

    if (operation === "lister") {
      afficherResultats(corps.resultats, corps);
    } else if (operation === "lire") {
      afficherResultats(corps.donnees);
    }
  } catch (erreur) {
    afficherMessage("erreur", `[ERREUR] Impossible de contacter l'API : ${erreur.message}`);
  } finally {
    boutonExecuter.disabled = false;
    boutonExecuter.textContent = "Exécuter";
  }
}

selecteurEntite.addEventListener("change", async () => {
  await chargerChampsEntite(selecteurEntite.value);
  genererChampsDonnees();
});
selecteurOperation.addEventListener("change", adapterFormulaireALOperation);
boutonExecuter.addEventListener("click", executerOperation);

/* ===================================================================
 * Requêtes SQL prédéfinies (lecture seule, paramétrées) - section 4.
 *
 * Principe : le Front-End ne connaît jamais le texte SQL. Il demande au
 * serveur (GET /requetes-sql) la liste des requêtes disponibles, chacune
 * avec son libellé et la liste de ses paramètres (un par "?"). Pour
 * chaque paramètre, un champ de saisie est généré dynamiquement - pas de
 * formulaire codé en dur par requête. Au clic sur "Exécuter la requête",
 * les valeurs saisies (dans le MÊME ORDRE que les paramètres) sont
 * envoyées au serveur, qui les transmet à pyodbc comme parametres
 * positionnels ("?") - jamais insérées dans le texte SQL lui-même (voir
 * connexion/requetes_sql_predefinies.py).
 * =================================================================== */

const selecteurRequeteSql = document.getElementById("selecteur-requete-sql");
const descriptionRequeteSql = document.getElementById("description-requete-sql");
const zoneParametresSql = document.getElementById("zone-parametres-sql");
const boutonExecuterSql = document.getElementById("bouton-executer-sql");
const zoneMessageSql = document.getElementById("zone-message-sql");
const zoneResultatsSql = document.getElementById("zone-resultats-sql");

let requetesSqlDisponibles = {};

/** Affiche un message [SUCCES]/[ERREUR]/[VALIDATION] sous la section SQL. */
function afficherMessageSql(type, texte) {
  zoneMessageSql.innerHTML = texte ? `<div class="message ${type}">${texte}</div>` : "";
}

/**
 * Objectif : construire dynamiquement un champ de saisie par paramètre
 * de la requête SQL choisie (un "?" = un champ, dans l'ordre).
 *
 * Chaque champ est un input texte avec une liste de suggestions
 * (<datalist>, l'équivalent HTML d'une ComboBox éditable) pré-remplie
 * avec la valeur d'exemple du paramètre, pour guider l'utilisateur sans
 * l'empêcher de saisir une autre valeur.
 */
function genererChampsParametresSql() {
  const nomRequete = selecteurRequeteSql.value;
  const infos = requetesSqlDisponibles[nomRequete];
  zoneParametresSql.innerHTML = "";
  zoneResultatsSql.innerHTML = "";
  afficherMessageSql("", "");

  if (!infos) {
    descriptionRequeteSql.textContent = "";
    return;
  }

  descriptionRequeteSql.textContent = infos.description || "";

  infos.parametres.forEach((parametre, index) => {
    const idChamp = `parametre-sql-${index}`;
    const idListe = `${idChamp}-suggestions`;

    const label = document.createElement("label");
    label.innerHTML = `
      ${parametre.nom}
      <input type="text" id="${idChamp}" list="${idListe}"
             placeholder="ex: ${parametre.exemple || ""}" />
      <datalist id="${idListe}">
        <option value="${parametre.exemple || ""}"></option>
      </datalist>
    `;
    zoneParametresSql.appendChild(label);
  });
}

/** Charge la liste des requêtes SQL prédéfinies (GET /requetes-sql). */
async function chargerRequetesSql() {
  try {
    const reponse = await fetch("/requetes-sql");
    const corps = await reponse.json();
    requetesSqlDisponibles = corps.requetes;
    selecteurRequeteSql.innerHTML = Object.entries(requetesSqlDisponibles)
      .map(([nom, infos]) => `<option value="${nom}">${infos.libelle}</option>`)
      .join("");
    genererChampsParametresSql();
  } catch (erreur) {
    selecteurRequeteSql.innerHTML = "<option value=''>(impossible de charger)</option>";
  }
}

/**
 * Objectif : executer la requête SQL choisie avec les valeurs saisies
 * dans les champs générés dynamiquement, puis afficher les résultats.
 */
async function executerRequeteSql() {
  const nomRequete = selecteurRequeteSql.value;
  const infos = requetesSqlDisponibles[nomRequete];
  if (!infos) {
    afficherMessageSql("validation", "[VALIDATION] Choisissez une requête.");
    return;
  }

  // Un parametre = un champ, lus DANS L'ORDRE de infos.parametres - c'est
  // cet ordre qui correspond a l'ordre des "?" dans le SQL cote serveur.
  const valeursParametres = infos.parametres.map((_, index) =>
    document.getElementById(`parametre-sql-${index}`).value.trim()
  );

  boutonExecuterSql.disabled = true;
  boutonExecuterSql.textContent = "Exécution en cours...";
  afficherMessageSql("", "");
  zoneResultatsSql.innerHTML = "";

  try {
    const reponse = await fetch(`/requetes-sql/${encodeURIComponent(nomRequete)}/executer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parametres: valeursParametres }),
    });
    const corps = await reponse.json();

    if (!reponse.ok) {
      afficherMessageSql(classeMessagePourErreur(corps.type), corps.erreur);
      return;
    }

    afficherMessageSql("succes", corps.message);
    if (corps.resultats.length === 0) {
      zoneResultatsSql.innerHTML = "<p>Aucun résultat.</p>";
    } else {
      const colonnes = Object.keys(corps.resultats[0]);
      const entetes = colonnes.map((c) => `<th>${c}</th>`).join("");
      const corpsTable = corps.resultats
        .map((ligne) => `<tr>${colonnes.map((c) => `<td>${ligne[c] ?? ""}</td>`).join("")}</tr>`)
        .join("");
      zoneResultatsSql.innerHTML = `<table><thead><tr>${entetes}</tr></thead><tbody>${corpsTable}</tbody></table>`;
    }
  } catch (erreur) {
    afficherMessageSql("erreur", `[ERREUR] Impossible de contacter l'API : ${erreur.message}`);
  } finally {
    boutonExecuterSql.disabled = false;
    boutonExecuterSql.textContent = "Exécuter la requête";
  }
}

selecteurRequeteSql.addEventListener("change", genererChampsParametresSql);
boutonExecuterSql.addEventListener("click", executerRequeteSql);

verifierConnexion();
chargerEntites();
chargerRequetesSql();
adapterFormulaireALOperation();
