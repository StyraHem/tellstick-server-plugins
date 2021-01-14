var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');

gulp.task('jsx', function () {
  return gulp.src('src/shelly/app/**/*.jsx')
    .pipe(babel({
      presets: ['es2015', 'stage-0', 'react']
    }))
    .pipe(gulp.dest('src/shelly/build'));
});

gulp.task('js', function () {
  return gulp.src('src/shelly/app/**/*.js')
    .pipe(gulp.dest('src/shelly/build'));
});

gulp.task('scripts', gulp.series('jsx', 'js', function () {
  return gulp.src('src/shelly/build/shelly/shelly.js')
    .pipe(requirejsOptimize({
      paths: {
        'react': 'empty:',
        'react-mdl': 'empty:',
        'react-router': 'empty:',
        'websocket': 'empty:',
        'telldus': 'empty:',
        'react-redux': 'empty:',
        'dialog-polyfill': 'empty:',        
      },
      baseUrl: 'src/shelly/build',
      name: 'shelly/shelly'
    }))
    .pipe(gulp.dest('src/shelly/htdocs'));
}));

gulp.task('default', gulp.series('scripts', function(done) {
	done();
}));

gulp.task('watch', gulp.series('default', function() {
  gulp.watch('src/shelly/app/**/*.jsx', ['default']);
}));
