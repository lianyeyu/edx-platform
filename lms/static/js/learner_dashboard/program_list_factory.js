;(function (define) {
    'use strict';

    define([
        'js/learner_dashboard/views/collection_list_view',
        'js/learner_dashboard/views/sidebar_view',
        'js/learner_dashboard/views/program_card_view',
        'js/learner_dashboard/collections/program_collection',
        'js/learner_dashboard/views/certificate_view'
    ],
    function (CollectionListView, SidebarView, ProgramCardView, ProgramCollection, CertificateView) {
        return function (options) {
            new CollectionListView({
                el: '.program-cards-container',
                childView: ProgramCardView,
                collection: new ProgramCollection(options.programsData)
            }).render();

            new SidebarView({
                el: '.sidebar',
                context: options
            }).render();

            new CertificateView(
                options.certificatesData
            ).render();

        };
    });
}).call(this, define || RequireJS.define);
