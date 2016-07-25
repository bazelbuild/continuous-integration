<?xml version='1.0' encoding='UTF-8'?>
<!--
  Copyright 2016 The Bazel Authors. All rights reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->
<project>
  <actions/>
  <description>Install Bazel on all the slaves</description>
  <keepDependencies>false</keepDependencies>
  <quietPeriod>0</quietPeriod>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <concurrentBuild>true</concurrentBuild>
  <builders>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="{{ variables.JENKINS_PLUGIN_conditional_buildstep }}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.ExpressionCondition" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}">
        <expression>(darwin|linux|ubuntu).*</expression>
        <label>${PLATFORM_NAME}</label>
      </condition>
      <buildStep class="hudson.tasks.Shell">
        <!-- Files copied are read-only, and jobs might fails because of that, clean-up. -->
        <command>rm -fr bazel-installer</command>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
    <hudson.plugins.copyartifact.CopyArtifact plugin="{{ variables.JENKINS_PLUGIN_copyartifact }}">
      <project>Bazel</project>
      <filter>**/ci/*installer*.sh,**/ci/bazel.exe</filter>
      <target>bazel-installer</target>
      <excludes></excludes>
      <selector class="hudson.plugins.copyartifact.TriggeredBuildSelector">
        <fallbackToLastSuccessful>true</fallbackToLastSuccessful>
        <upstreamFilterStrategy>UseGlobalSetting</upstreamFilterStrategy>
      </selector>
      <doNotFingerprintArtifacts>false</doNotFingerprintArtifacts>
    </hudson.plugins.copyartifact.CopyArtifact>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="{{ variables.JENKINS_PLUGIN_conditional_buildstep }}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.ExpressionCondition" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}">
        <expression>(darwin|linux|ubuntu).*</expression>
        <label>${PLATFORM_NAME}</label>
      </condition>
      <buildStep class="hudson.tasks.Shell">
	<command>{{ imports['//jenkins/jobs:Bazel-Install.sh.tpl'] }}</command>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
    <org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder plugin="{{ variables.JENKINS_PLUGIN_conditional_buildstep }}">
      <condition class="org.jenkins_ci.plugins.run_condition.core.ExpressionCondition" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}">
        <expression>windows.*</expression>
        <label>${PLATFORM_NAME}</label>
      </condition>
      <buildStep class="hudson.tasks.BatchFile">
        <command>{{ imports['//jenkins/jobs:Bazel-Install.bat.tpl'] }}</command>
      </buildStep>
      <runner class="org.jenkins_ci.plugins.run_condition.BuildStepRunner$Fail" plugin="{{ variables.JENKINS_PLUGIN_run_condition }}"/>
    </org.jenkinsci.plugins.conditionalbuildstep.singlestep.SingleConditionalBuilder>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>

