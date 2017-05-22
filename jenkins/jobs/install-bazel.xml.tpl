<?xml version='1.0' encoding='UTF-8'?>
<flow-definition>
  <actions/>
  <description>Job to install Bazel on all nodes</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>{{ imports['//jenkins/jobs:install-bazel.groovy'] }}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
</flow-definition>
