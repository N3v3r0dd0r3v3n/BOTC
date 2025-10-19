// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  auth: {
    client_id: 'xXxNjxJLkrnbgC1SB59K0BgPK06L5qvS',
    redirect_uri: 'http://localhost:4200/callback',
    scope: 'openid profile email offline_access',
    response_type: 'code',
    logout_redirect_uri: 'http://localhost:4200/logout'
  },
  botc_service_uri: 'http://localhost:8765/api',
  botc_service_ws: 'ws://localhost:8765/ws'
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
