pipeline {
  options {
    timestamps ()
    timeout(time: 1, unit: 'HOURS')
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }

  agent none

  stages {
    stage('Abort previous builds'){
      steps {
        milestone(Integer.parseInt(env.BUILD_ID)-1)
        milestone(Integer.parseInt(env.BUILD_ID))
      }
    }

    stage('Test & Build') {
      parallel {
        stage('Test') {
          agent {
            kubernetes {
              label 'python'
              defaultContainer 'python'
              yaml """
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: python
                    image: python:3.7
                    command: [cat]
                    tty: true
                    volumeMounts:
                      - { name: tmp, mountPath: /tmp }
                      - { name: docker, mountPath: /var/run/docker.sock }
                  volumes:
                    - name: tmp
                      hostPath: { path: /tmp, type: Directory }
                    - name: docker
                      hostPath: { path: /var/run/docker.sock, type: File }
                """
            }
          }

          steps {
            sh "apt update"
            sh "apt install -y python3-pip python3-dev build-essential gfortran musl-dev postgresql-contrib git curl netcat"

            dir("substrabac") {
              sh "pip install -r requirements.txt"
              sh "DJANGO_SETTINGS_MODULE=substrabac.settings.test coverage run manage.py test"
              sh "coverage report"
              sh "coverage html"
            }
          }

          post {
            success {
              publishHTML target: [
                allowMissing: false,
                alwaysLinkToLastBuild: false,
                keepAll: true,
                reportDir: 'substrabac/htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
              ]
            }
          }
        }

        stage('Build') {
          agent {
            kubernetes {
              label 'kaniko'
              yaml """
                apiVersion: v1
                kind: Pod
                metadata:
                  name: substrafront-build
                spec:
                  containers:
                  - name: kaniko
                    image: gcr.io/kaniko-project/executor:debug
                    command: [/busybox/cat]
                    tty: true
                    volumeMounts:
                    - name: kaniko-secret
                      mountPath: /secret
                    env:
                    - name: GOOGLE_APPLICATION_CREDENTIALS
                      value: /secret/kaniko-secret.json
                  volumes:
                    - name: kaniko-secret
                      secret:
                        secretName: kaniko-secret
                """
            }
          }

          steps {
            container(name:'kaniko', shell:'/busybox/sh') {
              sh '''#!/busybox/sh
                /kaniko/executor -f `pwd`/docker/substrabac/Dockerfile -c `pwd` -d "eu.gcr.io/substra-208412/substrabac:$GIT_COMMIT"
              '''
            }
          }
        }
      }
    }
  }
}
