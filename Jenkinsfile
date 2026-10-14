
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Jenkins has successfully checked out the repository!'
            }
        }

        stage('Verify') {
            steps {
                sh 'git --version'
                sh 'ls -la'
            }
        }
    }
}
