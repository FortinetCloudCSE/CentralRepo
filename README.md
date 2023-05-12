# Fortinet Hugo Customizations


### To run setup-gh-jenkins.sh (Create a New Workshop repo in https://github.com/FortinetCloudCSE with testing, and adding collaborator users )
Prerequisites: 
- Java Runtime
- GitHub CLI https://cli.github.com/manual/installation
    
    ```shell
    brew install java
    sudo ln -sfn /opt/homebrew/opt/openjdk/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk.jdk
    java --version
    
    brew install gh
    ```

1) Create an API token in Jenkins. http://jenkins.fortinetcloudcse.com:8080/

   - Navigate to Dashboard > Manage Jenkins > Manage Users > <User ID> > Configure
   - Under 'API Token', click 'Add new Token', enter a name for the token, and click 'Generate'.
   - Create a file in your home folder named .jenkins-cli, and paste the token into the file on the first line, with no whitespace or lines before or after.
     ```sh 
        cd ~HOME
        echo "pasted API Key" > .jenkins-cli
     ```

2) Download the Jenkins cli .jar file:
   - Open a browser and navigate to http://jenkins.fortinetcloudcse.com:8080/jnlpJars/jenkins-cli.jar
   - Copy the file to your home directory.
     ```shell
     mv Downloads/jenkins-cli.jar .
     ```

3) Verify that you can run commands with jenkins-cli.jar:

    ```shell
   java -jar ~/jenkins-cli.jar -s http://jenkins.fortinetcloudcse.com:8080/ -auth <your Jenkins user id>:$(cat ~/.jenkins-cli) list-jobs
    ```

4) Get the Jenkins Scripting via either of these methods
   - Clone from GitHub
    ```shell
    git clone git@github.com:rob-40net-test/cft-utility-templates.git
    ```
   - Copy the files manually from
        https://raw.githubusercontent.com/rob-40net-test/cft-utility-templates/main/jenkins/setup-gh-jenkins.sh
        https://raw.githubusercontent.com/rob-40net-test/cft-utility-templates/main/jenkins/template-config-params.xml
        https://raw.githubusercontent.com/rob-40net-test/cft-utility-templates/main/jenkins/template-config.xml

5) Authenticate to GH CLI with a PAT in the FortinetCloudCSE account. 
   ```shell 
   gh auth login
   ```
    Select "Github.com", and enter credentials when prompted.  Make sure you're using a *CLASSIC* Personal Access Token.
   - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
   - _*DO NOT USE A FINE GRAINED TOKEN*_

6) Run the Jenkins setup script to create a new TECWorkshop repo from the Parent Template & add collaborators:
    ```
    cd cft-utilitiy-templates/jenkins
    ./setup-gh-jenkins <Your Jenkins user id> <Name of Repo Template> <Name of New Repo to be created> <Github username of user to be added as collaborator> [-p]
    ```

    The -p flag is optional and will create a parameterized pipeline for terraform builds (functionality still being developed) in Jenkins.
