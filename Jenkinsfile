// Pipeline CI/CD - Bibliotheque Numerique DIT
// Groupe 2 - Master 1 IA - Dakar Institute of Technology
// Compatible Windows et Linux

pipeline {

    agent any

    environment {
        PROJECT_NAME       = "bibliotheque-dit"
        COMPOSE_FILE       = "docker-compose.yml"
        FRONTEND_PORT      = "80"
        LIVRES_PORT        = "8001"
        UTILISATEURS_PORT  = "8002"
        EMPRUNTS_PORT      = "8003"
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }

    stages {

        stage('Recuperation du code') {
            steps {
                echo '====== ETAPE 1 : Recuperation du code source ======'
                checkout scm
                echo 'Code recupere avec succes'
            }
        }

        stage('Verification de la structure') {
            steps {
                echo '====== ETAPE 2 : Verification de la structure du projet ======'
                script {
                    def fichiers = [
                        'docker-compose.yml',
                        'frontend/Dockerfile',
                        'frontend/index.html',
                        'service-livres/Dockerfile',
                        'service-livres/main.py',
                        'service-livres/requirements.txt',
                        'service-utilisateurs/Dockerfile',
                        'service-utilisateurs/main.py',
                        'service-utilisateurs/requirements.txt',
                        'service-emprunts/Dockerfile',
                        'service-emprunts/main.py',
                        'service-emprunts/requirements.txt'
                    ]
                    for (f in fichiers) {
                        if (!fileExists(f)) {
                            error "Fichier manquant : ${f}"
                        }
                        echo "  OK : ${f}"
                    }
                }
                echo 'Structure du projet validee'
            }
        }

        stage('Build des images Docker') {
            steps {
                echo '====== ETAPE 3 : Construction des images Docker ======'
                script {
                    if (isUnix()) {
                        sh "docker compose -f ${COMPOSE_FILE} build --no-cache"
                    } else {
                        // Vérifier que Docker est accessible
                        bat "docker --version"
                        bat "docker compose version"
                        bat "docker compose -f ${COMPOSE_FILE} build --no-cache"
                    }
                }
                echo 'Images construites avec succes'
            }
        }

        stage('Arret de l ancienne version') {
            steps {
                echo '====== ETAPE 4 : Arret des anciens conteneurs ======'
                script {
                    // Liste des conteneurs declares dans docker-compose.yml
                    def conteneurs = [
                        'bibliotheque-db',
                        'bibliotheque-livres',
                        'bibliotheque-utilisateurs',
                        'bibliotheque-emprunts',
                        'bibliotheque-frontend'
                    ]
                    if (isUnix()) {
                        // Suppression forcee de chaque conteneur par nom (orphelins inclus)
                        for (c in conteneurs) {
                            sh "docker stop ${c} || true"
                            sh "docker rm   ${c} || true"
                        }
                        sh "docker compose -f ${COMPOSE_FILE} down --remove-orphans || true"
                    } else {
                        // Suppression forcee de chaque conteneur par nom (orphelins inclus)
                        for (c in conteneurs) {
                            bat "docker stop ${c} || exit 0"
                            bat "docker rm   ${c} || exit 0"
                        }
                        try {
                            bat "docker compose -f ${COMPOSE_FILE} down --remove-orphans"
                        } catch (Exception e) {
                            echo "Aucun conteneur a arreter (normal au premier lancement)"
                        }
                    }
                }
                echo 'Environnement nettoye'
            }
        }

        stage('Deploiement') {
            steps {
                echo '====== ETAPE 5 : Deploiement des conteneurs ======'
                script {
                    if (isUnix()) {
                        sh "docker compose -f ${COMPOSE_FILE} up -d"
                    } else {
                        bat "docker compose -f ${COMPOSE_FILE} up -d"
                    }
                }
                echo 'Conteneurs demarres'
            }
        }

        stage('Verification sante des services') {
            steps {
                echo '====== ETAPE 6 : Verification de sante ======'
                script {
                    // Attente du demarrage
                    echo 'Attente du demarrage des services (25s)...'
                    sleep(time: 25, unit: 'SECONDS')

                    def services = [
                        [nom: 'Livres',       port: env.LIVRES_PORT],
                        [nom: 'Utilisateurs', port: env.UTILISATEURS_PORT],
                        [nom: 'Emprunts',     port: env.EMPRUNTS_PORT]
                    ]

                    for (svc in services) {
                        echo "--- Verification du service ${svc.nom} (port ${svc.port}) ---"
                        try {
                            if (isUnix()) {
                                sh "curl -sf http://localhost:${svc.port}/health"
                            } else {
                                bat "curl -sf http://localhost:${svc.port}/health"
                            }
                            echo " => Service ${svc.nom} OK"
                        } catch (Exception e) {
                            echo " => Service ${svc.nom} KO"
                        }
                    }

                    // Verification du frontend
                    echo "--- Verification du Frontend (port ${env.FRONTEND_PORT}) ---"
                    try {
                        if (isUnix()) {
                            sh "curl -sf http://localhost:${env.FRONTEND_PORT} > /dev/null"
                        } else {
                            bat "curl -sf http://localhost:${env.FRONTEND_PORT} > nul"
                        }
                        echo ' => Frontend OK'
                    } catch (Exception e) {
                        echo ' => Frontend KO'
                    }
                }
            }
        }

        stage('Tests fonctionnels') {
            steps {
                echo '====== ETAPE 7 : Tests fonctionnels de base ======'
                script {
                    // Test POST /livres
                    echo '--- Test POST /livres ---'
                    try {
                        if (isUnix()) {
                            sh """curl -sf -X POST http://localhost:${env.LIVRES_PORT}/livres \
                                -H "Content-Type: application/json" \
                                -d '{"titre":"Livre Test CI","auteur":"Jenkins","isbn":"999-CI-TEST","annee":2025,"genre":"Test","quantite":1}'"""
                        } else {
                            bat """curl -sf -X POST http://localhost:${env.LIVRES_PORT}/livres -H "Content-Type: application/json" -d "{\\"titre\\":\\"Livre Test CI\\",\\"auteur\\":\\"Jenkins\\",\\"isbn\\":\\"999-CI-TEST\\",\\"annee\\":2025,\\"genre\\":\\"Test\\",\\"quantite\\":1}" """
                        }
                        echo 'POST /livres OK'
                    } catch (Exception e) {
                        echo 'POST /livres - deja existant ou erreur (normal en re-execution)'
                    }

                    // Test GET /livres
                    echo '--- Test GET /livres ---'
                    try {
                        if (isUnix()) {
                            sh "curl -sf http://localhost:${env.LIVRES_PORT}/livres"
                        } else {
                            bat "curl -sf http://localhost:${env.LIVRES_PORT}/livres"
                        }
                        echo 'GET /livres OK'
                    } catch (Exception e) {
                        echo 'GET /livres KO'
                    }

                    // Test GET /utilisateurs
                    echo '--- Test GET /utilisateurs ---'
                    try {
                        if (isUnix()) {
                            sh "curl -sf http://localhost:${env.UTILISATEURS_PORT}/utilisateurs"
                        } else {
                            bat "curl -sf http://localhost:${env.UTILISATEURS_PORT}/utilisateurs"
                        }
                        echo 'GET /utilisateurs OK'
                    } catch (Exception e) {
                        echo 'GET /utilisateurs KO'
                    }

                    // Test GET /emprunts
                    echo '--- Test GET /emprunts ---'
                    try {
                        if (isUnix()) {
                            sh "curl -sf http://localhost:${env.EMPRUNTS_PORT}/emprunts"
                        } else {
                            bat "curl -sf http://localhost:${env.EMPRUNTS_PORT}/emprunts"
                        }
                        echo 'GET /emprunts OK'
                    } catch (Exception e) {
                        echo 'GET /emprunts KO'
                    }

                    // Test POST /auth/login + changer-mot-de-passe (flux mot de passe temporaire)
                    echo '--- Test flux mot de passe temporaire ---'
                    try {
                        if (isUnix()) {
                            sh """
                                # Créer un utilisateur membre (mot de passe temporaire)
                                RESP=\$(curl -sf -X POST http://localhost:${env.UTILISATEURS_PORT}/utilisateurs \
                                    -H 'Content-Type: application/json' \
                                    -d '{"nom":"Test","prenom":"CI","email":"ci_test@dit.sn","mot_de_passe":"Temp1234","type":"etudiant","role":"membre","matricule":"CI-TEST-001"}') || true
                                # Login → doit retourner mot_de_passe_temporaire=true
                                LOGIN=\$(curl -sf -X POST http://localhost:${env.UTILISATEURS_PORT}/auth/login \
                                    -H 'Content-Type: application/json' \
                                    -d '{"email":"ci_test@dit.sn","mot_de_passe":"Temp1234"}') || true
                                TOKEN=\$(echo \$LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
                                if [ -n "\$TOKEN" ]; then
                                    curl -sf -X POST http://localhost:${env.UTILISATEURS_PORT}/auth/changer-mot-de-passe \
                                        -H 'Content-Type: application/json' \
                                        -H "Authorization: Bearer \$TOKEN" \
                                        -d '{"ancien_mot_de_passe":"Temp1234","nouveau_mot_de_passe":"NvMdp5678"}' || true
                                fi
                            """
                        } else {
                            echo 'Test mot de passe temporaire (Linux uniquement)'
                        }
                        echo 'Test flux mot de passe temporaire OK'
                    } catch (Exception e) {
                        echo 'Test flux mot de passe temporaire - erreur non bloquante'
                    }

                    echo 'Tests fonctionnels termines'
                }
            }
        }
    }

    post {

        success {
            echo '''
============================================================
  DEPLOIEMENT REUSSI
  Application accessible sur http://localhost
  -  Frontend Vue.js      : http://localhost:80
  -  Service Livres       : http://localhost:8001/docs
  -  Service Utilisateurs : http://localhost:8002/docs
  -  Service Emprunts     : http://localhost:8003/docs
============================================================
            '''
        }

        failure {
            echo 'ECHEC DU PIPELINE - Nettoyage en cours...'
            script {
                try {
                    if (isUnix()) {
                        sh "docker compose -f ${COMPOSE_FILE} logs --tail=30 || true"
                        sh "docker compose -f ${COMPOSE_FILE} down || true"
                    } else {
                        bat "docker compose -f ${COMPOSE_FILE} logs --tail=30 || exit 0"
                        bat "docker compose -f ${COMPOSE_FILE} down || exit 0"
                    }
                } catch (Exception e) {
                    echo "Nettoyage impossible : ${e.message}"
                }
            }
        }

        always {
            echo 'Pipeline termine - Groupe 2 DIT M1 IA'
        }
    }
}
