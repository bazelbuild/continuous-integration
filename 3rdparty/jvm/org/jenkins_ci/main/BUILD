java_library(
    name = "cli",
    exports = [
        "//external:jar/org/jenkins_ci/main/cli"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "jenkins_core",
    exports = [
        "//external:jar/org/jenkins_ci/main/jenkins_core"
    ],
    runtime_deps = [
        "//3rdparty/jvm/antlr:antlr",
        "//3rdparty/jvm/args4j:args4j",
        "//3rdparty/jvm/com/github/jnr:jnr_posix",
        "//3rdparty/jvm/com/google/guava:guava",
        "//3rdparty/jvm/com/google/inject:guice",
        "//3rdparty/jvm/com/infradna/tool:bridge_method_annotation",
        "//3rdparty/jvm/com/jcraft:jzlib",
        "//3rdparty/jvm/com/sun/solaris:embedded_su4j",
        "//3rdparty/jvm/com/sun/xml/txw2:txw2",
        "//3rdparty/jvm/commons_beanutils:commons_beanutils",
        "//3rdparty/jvm/commons_codec:commons_codec",
        "//3rdparty/jvm/commons_collections:commons_collections",
        "//3rdparty/jvm/commons_digester:commons_digester",
        "//3rdparty/jvm/commons_fileupload:commons_fileupload",
        "//3rdparty/jvm/commons_httpclient:commons_httpclient",
        "//3rdparty/jvm/commons_io:commons_io",
        "//3rdparty/jvm/commons_jelly:commons_jelly_tags_fmt",
        "//3rdparty/jvm/commons_jelly:commons_jelly_tags_xml",
        "//3rdparty/jvm/commons_lang:commons_lang",
        "//3rdparty/jvm/javax/mail:mail",
        "//3rdparty/jvm/javax/servlet/jsp/jstl:javax_servlet_jsp_jstl_api",
        "//3rdparty/jvm/jaxen:jaxen",
        "//3rdparty/jvm/jfree:jfreechart",
        "//3rdparty/jvm/jline:jline",
        "//3rdparty/jvm/net/java/dev/jna:jna",
        "//3rdparty/jvm/net/java/sezpoz:sezpoz",
        "//3rdparty/jvm/net/sf/kxml:kxml2",
        "//3rdparty/jvm/org/acegisecurity:acegi_security",
        "//3rdparty/jvm/org/apache/ant:ant",
        "//3rdparty/jvm/org/apache/commons:commons_compress",
        "//3rdparty/jvm/org/codehaus/groovy:groovy_all",
        "//3rdparty/jvm/org/codehaus/woodstox:wstx_asl",
        "//3rdparty/jvm/org/fusesource/jansi:jansi",
        "//3rdparty/jvm/org/jenkins_ci/plugins/icon_shim:icon_set",
        "//3rdparty/jvm/org/jenkins_ci:annotation_indexer",
        "//3rdparty/jvm/org/jenkins_ci:bytecode_compatibility_transformer",
        "//3rdparty/jvm/org/jenkins_ci:commons_jexl",
        "//3rdparty/jvm/org/jenkins_ci:crypto_util",
        "//3rdparty/jvm/org/jenkins_ci:jmdns",
        "//3rdparty/jvm/org/jenkins_ci:memory_monitor",
        "//3rdparty/jvm/org/jenkins_ci:symbol_annotation",
        "//3rdparty/jvm/org/jenkins_ci:task_reactor",
        "//3rdparty/jvm/org/jenkins_ci:trilead_ssh2",
        "//3rdparty/jvm/org/jenkins_ci:version_number",
        "//3rdparty/jvm/org/jruby/ext/posix:jna_posix",
        "//3rdparty/jvm/org/jvnet/hudson:activation",
        "//3rdparty/jvm/org/jvnet/hudson:commons_jelly_tags_define",
        "//3rdparty/jvm/org/jvnet/hudson:jtidy",
        "//3rdparty/jvm/org/jvnet/hudson:xstream",
        "//3rdparty/jvm/org/jvnet/localizer:localizer",
        "//3rdparty/jvm/org/jvnet/robust_http_client:robust_http_client",
        "//3rdparty/jvm/org/jvnet/winp:winp",
        "//3rdparty/jvm/org/kohsuke/jinterop:j_interop",
        "//3rdparty/jvm/org/kohsuke/stapler:json_lib",
        "//3rdparty/jvm/org/kohsuke/stapler:stapler_adjunct_codemirror",
        "//3rdparty/jvm/org/kohsuke/stapler:stapler_adjunct_timeline",
        "//3rdparty/jvm/org/kohsuke/stapler:stapler_adjunct_zeroclipboard",
        "//3rdparty/jvm/org/kohsuke/stapler:stapler_groovy",
        "//3rdparty/jvm/org/kohsuke/stapler:stapler_jrebel",
        "//3rdparty/jvm/org/kohsuke:access_modifier_annotation",
        "//3rdparty/jvm/org/kohsuke:akuma",
        "//3rdparty/jvm/org/kohsuke:libpam4j",
        "//3rdparty/jvm/org/kohsuke:libzfs",
        "//3rdparty/jvm/org/kohsuke:trilead_putty_extension",
        "//3rdparty/jvm/org/kohsuke:windows_package_checker",
        "//3rdparty/jvm/org/slf4j:jcl_over_slf4j",
        "//3rdparty/jvm/org/slf4j:log4j_over_slf4j",
        "//3rdparty/jvm/org/springframework:spring_aop",
        "//3rdparty/jvm/org/springframework:spring_core",
        "//3rdparty/jvm/org/springframework:spring_webmvc",
        "//3rdparty/jvm/xpp3:xpp3",
        ":cli",
        ":remoting"
    ],
    visibility = [
        "//visibility:public"
    ]
)



java_library(
    name = "remoting",
    exports = [
        "//external:jar/org/jenkins_ci/main/remoting"
    ],
    runtime_deps = [
        "//3rdparty/jvm/org/jenkins_ci:constant_pool_scanner"
    ],
    visibility = [
        "//visibility:public"
    ]
)


