
pipeline {
    agent any

    environment {
        PATH = "/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }

    stages {
        stage('Check Environment') {
            steps {
                sh '''
                    whoami
                    docker version
                    docker compose version
                '''
            }
        }

        stage('Validate Compose') {
            steps {
                sh 'docker compose config --quiet'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker compose build'
            }
        }
    }

    post {
        success {
            echo 'CI pipeline passed: Compose is valid and images built.'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}
