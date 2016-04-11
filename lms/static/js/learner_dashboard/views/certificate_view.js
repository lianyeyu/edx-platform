;(function (define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/certificate.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             certificateTpl
         ) {
            return Backbone.View.extend({
                el: '.certificates-list',
                tpl: _.template(certificateTpl),
                initialize: function(certificatesData) {
                    this.certificatesData = certificatesData;
                },
                render: function() {
                    if (this.certificatesData.length > 0) {
                        this.$el.html(this.tpl({certificates: this.certificatesData}));
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
