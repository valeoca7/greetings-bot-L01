pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
    }

    environment {
        PYTHONDONTWRITEBYTECODE = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Check') {
            steps {
                sh 'make check'
            }
        }

        stage('Package') {
            steps {
                sh 'make check-package'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'dist/*.tar.gz', allowEmptyArchive: true,
                fingerprint: true
        }
    }
}
