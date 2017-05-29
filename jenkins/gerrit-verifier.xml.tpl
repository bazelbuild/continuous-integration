<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>-1</daysToKeep>
        <numToKeep>25</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    {% if variables.production == "true" %}
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <hudson.triggers.TimerTrigger>
          <spec>* * * * *</spec>
        </hudson.triggers.TimerTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
    {% endif %}
  </properties>
  <assignedNode>deploy</assignedNode>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>{{ imports['//jenkins:gerrit-verifier.groovy'] }}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
