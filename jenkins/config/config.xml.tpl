<?xml version='1.0' encoding='UTF-8'?>
<hudson>
  <disabledAdministrativeMonitors>
    <string>hudson.diagnosis.ReverseProxySetupMonitor</string>
  </disabledAdministrativeMonitors>
  <version>1.609.2</version>
  <numExecutors>0</numExecutors>
  <mode>NORMAL</mode>
  {{ variables.SECURITY_CONFIG }}
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
    <listView>
      <owner class="hudson" reference="../../.."/>
      <name>Projects</name>
      <description>All projects</description>
      <filterExecutors>false</filterExecutors>
      <filterQueue>false</filterQueue>
      <properties class="hudson.model.View$PropertyList"/>
      <jobNames>
        {% for v in variables.GITHUB_JOBS.split(", ") %}<string>{{ v }}</string>{% endfor %}
      </jobNames>
      <jobFilters/>
      <columns>
        <hudson.views.StatusColumn/>
        <hudson.views.WeatherColumn/>
        <hudson.views.JobColumn/>
        <hudson.views.LastSuccessColumn/>
        <hudson.views.LastFailureColumn/>
        <hudson.views.LastDurationColumn/>
        <hudson.views.BuildButtonColumn/>
      </columns>
      <recurse>false</recurse>
    </listView>
    <listView>
      <owner class="hudson" reference="../../.."/>
      <name>Bazel bootstrap and maintenance</name>
      <filterExecutors>false</filterExecutors>
      <filterQueue>false</filterQueue>
      <properties class="hudson.model.View$PropertyList"/>
      <jobNames>
        {% for v in variables.BAZEL_JOBS.split(", ") %}<string>{{ v }}</string>{% endfor %}
      </jobNames>
      <jobFilters/>
      <columns>
        <hudson.views.StatusColumn/>
        <hudson.views.WeatherColumn/>
        <hudson.views.JobColumn/>
        <hudson.views.LastSuccessColumn/>
        <hudson.views.LastFailureColumn/>
        <hudson.views.LastDurationColumn/>
        <hudson.views.BuildButtonColumn/>
      </columns>
      <recurse>false</recurse>
    </listView>
    <com.smartcodeltd.jenkinsci.plugins.buildmonitor.BuildMonitorView>
      <owner class="hudson" reference="../../.."/>
      <name>Dashboard</name>
      <filterExecutors>false</filterExecutors>
      <filterQueue>false</filterQueue>
      <properties class="hudson.model.View$PropertyList"/>
      <jobNames>
        <comparator class="hudson.util.CaseInsensitiveComparator"/>
        <string>Bazel</string>
        <string>Bazel-Install-Trigger</string>
        <string>Bazel-Publish-Site</string>
        {% for v in variables.GITHUB_JOBS.split(", ") %}<string>{{ v }}</string>{% endfor %}
      </jobNames>
      <jobFilters/>
      <columns/>
      <recurse>true</recurse>
      <title>Dashboard</title>
      <config>
        <displayCommitters>false</displayCommitters>
        <order class="com.smartcodeltd.jenkinsci.plugins.buildmonitor.order.ByName"/>
      </config>
    </com.smartcodeltd.jenkinsci.plugins.buildmonitor.BuildMonitorView>
  </views>
  <primaryView>Projects</primaryView>
  <nodeProperties/>
  <globalNodeProperties/>
</hudson>
