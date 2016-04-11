/**
 * Model for Course Programs.
 */
(function (define) {
    'use strict';
    define([
            'backbone'
        ],
        function (Backbone) {
            return Backbone.Model.extend({
                initialize: function(data) {
                    if (data){
                        this.set({
                            display_name: data.display_name,
                            url: data.credential_url
                        });
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
