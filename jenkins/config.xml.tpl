<?xml version='1.0' encoding='UTF-8'?>
<hudson>
  <disabledAdministrativeMonitors>
    <string>hudson.diagnosis.ReverseProxySetupMonitor</string>
  </disabledAdministrativeMonitors>
  <version>1.609.2</version>
  <numExecutors>0</numExecutors>
  <mode>NORMAL</mode>
  <!-- For testing without security, set "useSecurity" to false -->
  <useSecurity>true</useSecurity>
  <authorizationStrategy class="hudson.security.GlobalMatrixAuthorizationStrategy">
    %{JENKINS_PERMISSIONS}
  </authorizationStrategy>
  <securityRealm class="org.jenkinsci.plugins.googlelogin.GoogleOAuth2SecurityRealm" plugin="google-login@1.1">
    <clientId>##SECRET:google.oauth.clientid##</clientId>
    <clientSecret>##SECRET:google.oauth.secret##</clientSecret>
    <domain>google.com</domain>
  </securityRealm>
  <!-- end of security settings-->
  <disableRememberMe>false</disableRememberMe>
  <projectNamingStrategy class="jenkins.model.ProjectNamingStrategy$DefaultProjectNamingStrategy"/>
  <workspaceDir>${JENKINS_HOME}/workspace/${ITEM_FULLNAME}</workspaceDir>
  <buildsDir>${ITEM_ROOTDIR}/builds</buildsDir>
  <markupFormatter class="hudson.markup.EscapedMarkupFormatter"/>
  <jdks/>
  <viewsTabBar class="hudson.views.DefaultViewsTabBar"/>
  <myViewsTabBar class="hudson.views.DefaultMyViewsTabBar"/>
  <clouds/>
  <quietPeriod>5</quietPeriod>
  <scmCheckoutRetryCount>0</scmCheckoutRetryCount>
  <views>
    <hudson.model.AllView>
      <owner class="hudson" reference="../../.."/>
      <name>All</name>
      <filterExecutors>false</filterExecutors>
      <filterQueue>false</filterQueue>
      <properties class="hudson.model.View$PropertyList"/>
    </hudson.model.AllView>
  </views>
  <primaryView>All</primaryView>
  <nodeProperties/>
  <globalNodeProperties/>
</hudson>
