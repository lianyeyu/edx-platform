define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/certificate_view',
        'js/learner_dashboard/models/certificate_model'
    ], function (Backbone, $, CertificateView, CertificateModel) {
        
        'use strict';
        /*jslint maxlen: 500 */
        
        describe('Certificate View', function () {
            var view = null,
                certificate = {
                    certificatesData: [
                        {
                            "display_name": "Testing",
                            "credential_url": "https://credentials.stage.edx.org/credentials/45667/"
                        },
                        {
                            "display_name": "Testing2",
                            "credential_url": "https://credentials.stage.edx.org/credentials/12345/"
                        }
                    ]
                };

            beforeEach(function() {
                setFixtures('<div class="certificates-list"></div>');
                view = new CertificateView(certificate.certificatesData);
                view.render();
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should load the certificates based on passed in certificates list', function() {
                var $certificate = view.$el.find('.certificate-box');
                expect($certificate.length).toBe(2);
                $certificate.each(function(index, el){
                    expect($(el).find('.copy').html().trim()).toEqual(certificate.certificatesData[index].display_name);
                    expect($(el).find('.copy').attr('href')).toEqual(certificate.certificatesData[index].credential_url);
                });
                expect(view.$el.find('.title').html().trim()).toEqual('XSeries Program Certificates:');
            });

             it('should display no certificate box if certificates list is empty', function() {
                view.remove();
                setFixtures('<div class="certificates-list"></div>');
                view = new CertificateView([]);
                view.render();
                var $certificate = view.$el.find('.certificate-box');
                expect($certificate.length).toBe(0);
            });
        });
    }
);
