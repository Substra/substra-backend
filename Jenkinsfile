pipeline {
  options {
    timestamps ()
    timeout(time: 1, unit: 'HOURS')
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }

  parameters {
    booleanParam(name: 'E2E', defaultValue: false, description: 'Launch E2E test')
    string(name: 'CLI', defaultValue: 'dev', description: 'substra-cli branch')
    string(name: 'CHAINCODE', defaultValue: 'dev', description: 'chaincode branch')

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
        stage('Test Helm') {
          agent {
            kubernetes {
              label 'substra-backend-helm'
              defaultContainer 'helm'
              yamlFile '.cicd/agent-helm.yaml'
            }
          }

          steps {
            sh "helm lint charts/substra-backend"
          }
        }

        stage('Test') {
          agent {
            kubernetes {
              label 'substrabac-test'
              defaultContainer 'python'
              yamlFile '.cicd/agent-python.yaml'
            }
          }

          steps {
            sh "apt update"
            sh "apt install curl && mkdir -p /tmp/download && curl -L https://download.docker.com/linux/static/stable/x86_64/docker-18.06.3-ce.tgz | tar -xz -C /tmp/download && mv /tmp/download/docker/docker /usr/local/bin/"
            sh "docker login -u _json_key --password-stdin https://eu.gcr.io/substra-208412/ < /secret/kaniko-secret.json"
            sh "apt install -y python3-pip python3-dev build-essential gfortran musl-dev postgresql-contrib git curl netcat"

            dir("substra-backend") {
              sh "pip install flake8"
              sh "flake8"
              sh "pip install -r requirements.txt"
              sh "DJANGO_SETTINGS_MODULE=substrabackend.settings.test coverage run manage.py test"
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
                reportDir: 'substra-backend/htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
              ]
            }
          }
        }

        stage('Build substra-backend') {
          agent {
            kubernetes {
              label 'substra-backend-kaniko-substrabackend'
              yamlFile '.cicd/agent-kaniko.yaml'
            }
          }

          steps {
            container(name:'kaniko', shell:'/busybox/sh') {
              sh '''#!/busybox/sh
                /kaniko/executor -f `pwd`/docker/substra-backend/Dockerfile -c `pwd` -d "eu.gcr.io/substra-208412/substra-backend:$GIT_COMMIT"
              '''
            }
          }
        }

        stage('Build celerybeat') {
          agent {
            kubernetes {
              label 'substrabac-kaniko-celerybeat'
              yamlFile '.cicd/agent-kaniko.yaml'
            }
          }

          steps {
            container(name:'kaniko', shell:'/busybox/sh') {
              sh '''#!/busybox/sh
                /kaniko/executor -f `pwd`/docker/celerybeat/Dockerfile -c `pwd` -d "eu.gcr.io/substra-208412/celerybeat:$GIT_COMMIT"
              '''
            }
          }
        }

        stage('Build celeryworker') {
          agent {
            kubernetes {
              label 'substrabac-kaniko-celeryworker'
              yamlFile '.cicd/agent-kaniko.yaml'
            }
          }

          steps {
            container(name:'kaniko', shell:'/busybox/sh') {
              sh '''#!/busybox/sh
                /kaniko/executor -f `pwd`/docker/celeryworker/Dockerfile -c `pwd` -d "eu.gcr.io/substra-208412/celeryworker:$GIT_COMMIT"
              '''
            }
          }
        }

        stage('Publish Helm') {
          agent {
            kubernetes {
              label 'substra-backend-helm'
              defaultContainer 'helm'
              yamlFile '.cicd/agent-helm.yaml'
            }
          }

          when { buildingTag() }

          steps {
            sh "helm init --client-only"
            sh "helm plugin install https://github.com/chartmuseum/helm-push"
            sh "helm repo add substra https://substra-charts.owkin.com --username owlways --password Cokear4nnRK9ooC"
            sh "helm push charts/substra-backend substra || true"
          }
        }
      }
    }

    stage('Test with substra-network') {
      when {
        expression { return params.E2E }
      }

      steps {
        build job: 'substra-network/dev', parameters: [string(name: 'BACKEND', value: env.CHANGE_BRANCH),
                                                       string(name: 'CHAINCODE', value: params.CHAINCODE),
                                                       string(name: 'CLI', value: params.CLI)], propagate: true
      }
    }

  }
}
