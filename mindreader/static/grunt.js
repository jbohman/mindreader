module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib');

  // Project configuration.
  grunt.initConfig({
    lint: {
      files: ['grunt.js', 'src/**/*.js']
    },
    less: {
      dist: {
        files: {
          'src/css/base.css': 'src/less/base.less' 
        }     
      }
    },
    concat: {
      dist: {
        src: ['src/sound.js'],
        dest: 'dist/core.js'
      },
      css: {
        src: ['src/css/*.css'],
        dest: 'dist/css/main.css'
      }
    },
    min: {
      dist: {
        src: ['dist/core.js'],
        dest: 'dist/core.min.js',
        seperator: ','
      }
    },
    mincss: {
      'dist/css/main.min.css': ['dist/css/main.css']
    },
    watch: {
      files: "<config:lint.all>",
      tasks: "development"
    },
    copy: {
      dist: {
        options: {
          'flatten': true
        },
        files: {
          '../static/css/': 'dist/**/*.css',
          '../static/js/': 'dist/*.js'
        }
      }
    },
    jshint: {
      options: {
        curly: true,
        eqeqeq: true,
        immed: true,
        latedef: true,
        newcap: true,
        noarg: true,
        sub: true,
        //undef: true,
        boss: true,
        eqnull: true,
        browser: true,
        devel: true
      },
      globals: {
        jQuery: true
      }
    }
  });

  grunt.registerTask('default', 'lint');
  grunt.registerTask('production', 'lint less concat min mincss copy');
  grunt.registerTask('development', 'lint less concat copy');

};
