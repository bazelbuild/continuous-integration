<?xml version='1.0' encoding='UTF-8'?>
<matrix-project plugin="%{JENKINS_PLUGIN_matrix-project}">
  <actions/>
  <description>Incremental build for testing Pull Request and Gerrit reviews&#xd;
&#xd;
Note: because this can potentially run 3rd party code, the security of this one should be ensure: run on independent VM, enable test sandboxing, etc...&#xd;
&#xd;
For gerrit review (https://wiki.jenkins-ci.org/display/JENKINS/Gerrit+Trigger) we could make it happens on a +1 review from a core contributors.&#xd;
On github I don&apos;t know, maybe manually&#xd;
&#xd;
TODO: link to Gerrit review, Github PR. +1 / -1 on Gerrit reviews. Message on Github PR. Maybe split in two jobs (PR / Gerrit review)</description>
  <logRotator class="hudson.tasks.LogRotator">
    <daysToKeep>30</daysToKeep>
    <numToKeep>-1</numToKeep>
    <artifactDaysToKeep>-1</artifactDaysToKeep>
    <artifactNumToKeep>-1</artifactNumToKeep>
  </logRotator>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="{JENKINS_PLUGIN_github}">
      <projectUrl>%{GITHUB_URL}</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
  </properties>
  <scm class="hudson.plugins.git.GitSCM" plugin="%{JENKINS_PLUGIN_git}">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <url>%{GITHUB_URL}</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>*/master</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
    <browser class="hudson.plugins.git.browser.AssemblaWeb">
      <url></url>
    </browser>
    <submoduleCfg class="list"/>
    <extensions/>
  </scm>
  <quietPeriod>5</quietPeriod>
  <assignedNode>safe</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <axes>
    <hudson.matrix.LabelAxis>
      <name>PLATFORM_NAME</name>
      <values>%{PLATFORMS}</values>
    </hudson.matrix.LabelAxis>
  </axes>
  <builders>
    <hudson.plugins.copyartifact.CopyArtifact plugin="%{JENKINS_PLUGIN_copyartifact}">
      <project>Bazel</project>
      <filter>**/*-bazel</filter>
      <target>output</target>
      <excludes></excludes>
      <selector class="hudson.plugins.copyartifact.StatusBuildSelector">
        <stable>true</stable>
      </selector>
      <flatten>true</flatten>
      <doNotFingerprintArtifacts>false</doNotFingerprintArtifacts>
    </hudson.plugins.copyartifact.CopyArtifact>
    <hudson.tasks.Shell>
      <command>EMBED_LABEL=
BAZEL=$(find output -name ${PLATFORM_NAME}-bazel)
chmod 0755 ${BAZEL}
BAZELRC=$PWD/output/bazelrc
cat &lt;&lt;&apos;EOF&apos; &gt;${BAZELRC}
build --nostamp
EOF

./compile.sh tools ${BAZEL} # Make sure the tools are bootstrapped.

&quot;${BAZEL}&quot; --nomaster_blazerc --bazelrc=/dev/null --watchfs \
  test --test_output=errors --nostamp \
  //scripts/... //src/... //third_party/...</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
  <executionStrategy class="hudson.matrix.DefaultMatrixExecutionStrategyImpl">
    <runSequentially>false</runSequentially>
  </executionStrategy>
</matrix-project>
