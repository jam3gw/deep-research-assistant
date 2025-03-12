export interface EnvironmentConfig {
    name: string;
    domainName: string;
    tags: Record<string, string>;
}

export interface AppConfig {
    hostedZoneName: string;
    environments: Record<string, EnvironmentConfig>;
}

const config: AppConfig = {
    hostedZoneName: 'jake-moses.com',
    environments: {
        dev: {
            name: 'dev',
            domainName: 'deep-research-assistant.dev.jake-moses.com',
            tags: {
                Environment: 'development',
                Project: 'PersonalAssistant'
            }
        },
        prod: {
            name: 'prod',
            domainName: 'deep-research-assistant.jake-moses.com',
            tags: {
                Environment: 'production',
                Project: 'PersonalAssistant'
            }
        }
    }
};

export default config; 