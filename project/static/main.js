(function () {

  'use strict';

  angular.module('DownloaderApp', ['ui.toggle'])

  .controller('DownloaderController', ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {
      var timeout = "";

      $scope.playlistToggle = function () {
        console.log($scope.playlist);  // TODO open extended playlist download controls
      };
      
      $scope.addDownload = function () {
        $http.post('/api/add', {
          'url': $scope.url,
          'format': $scope.format,
          'path': $scope.path,
          'extendedPath': $scope.extendedPath,
          'playlist': $scope.playlist
        }).success(function (results) {
          $log.log(results);
          $('#url-box').val('');
          $('#url-box').attr('rows', 1);
        }).error(function (error) {
          $log.log(error);
        });
      };
      
      $scope.deleteDownload = function (id) {
        $http.delete('/api/remove/' + id).success(function (results) {
          $log.log(results);
        }).error(function (error) {
          $log.log(error);
        });
      };
      
      $scope.restartDownload = function (id) {
        $http.post('/api/restart/' + id).success(function (results) {
          $log.log(results);
        }).error(function (error) {
          $log.log(error);
        })
      };
      
      $scope.getDownloads = function () {
        $http.get('/api/downloads').success(function (results) {
          $scope.downloads = results.data;
          timeout = $timeout($scope.getDownloads, 2000);
        }).error(function (error) {
          $log.log(error);
          $timeout.cancel(timeout);
        });
      };
      
      $scope.getFormats = function () {
        $http.get('/api/formats').success(function (results) {
          $scope.formats = results.data;
          $scope.format = results.data[0].name;
        }).error(function (error) {
          $log.log(error);
        });
      };

      $scope.getPaths = function () {
        $http.get('/api/paths').success(function (results) {
          $scope.paths = results.data;
          $scope.path = results.data[0];
        }).error(function (error) {
          $log.log(error)
        });
      };
      
      $scope.getFormats();

      $scope.getPaths();
      
      $scope.getDownloads();
      
      $scope.$watch('url', function () {
        $('#url-box').attr('rows', $('#url-box').val().split('\n').length);
      });
      
    }])
      .filter('bytes', function() {
        return function(bytes, precision) {
          if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
          if (typeof precision === 'undefined') precision = 1;
          var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
            number = Math.floor(Math.log(bytes) / Math.log(1024));
          return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
        }
      });

}());
