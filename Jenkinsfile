pipeline {
  options {
    timestamps ()
    timeout(time: 1, unit: 'HOURS')
    retry(2)
  }

  agent none

  stages {
    stage('Abort previous builds'){
      steps {
        milestone(Integer.parseInt(env.BUILD_ID)-1)
        milestone(Integer.parseInt(env.BUILD_ID))
      }
    }

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
                securityContext:
                  privileged: true
                volumeMounts:
                  - name: tmp
                    mountPath: /tmp
                  - name: docker
                    mountPath: /var/run/docker.sock
              volumes:
                - name: tmp
                  hostPath:
                    path: /tmp
                    type: Directory
                - name: docker
                  hostPath:
                    path: /var/run/docker.sock
                    type: File
            """
        }
      }

      steps {
        sh "apt update"
        sh "apt install -y python3-pip python3-dev build-essential gfortran musl-dev postgresql-contrib git curl netcat"
        sh "make test"
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
          label 'docker'
          defaultContainer 'docker'
          yaml """
            apiVersion: v1
            kind: Pod
            spec:
              containers:
              - name: docker
                image: docker:dind
                command: [cat]
                tty: true
                securityContext:
                  privileged: true
            """
        }
      }

      steps {
        sh "apk add --update make"
        sh "make build"
      }
    }
  }
}
