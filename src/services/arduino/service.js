/**
 * Arduino Service
 * Service layer for Arduino spoofing functionality
 */

const { logger } = require('../../core/logger');
const { ErrorHandler } = require('../../core/errors');
const { ArduinoCollector } = require('../../modules/arduino/collector');

class ArduinoService {
    constructor() {
        this.collector = null;
        this.initialized = false;
        this.collectionResults = null;
    }

    /**
     * Initialize Arduino service
     * @returns {Promise<void>}
     */
    async initialize() {
        try {
            logger.info('Initializing Arduino service');

            this.collector = new ArduinoCollector();
            const initSuccess = await this.collector.initialize();

            this.initialized = initSuccess;

            if (this.initialized) {
                logger.info('Arduino service initialized successfully');
            } else {
                logger.warn('Arduino service initialization failed, service will be disabled');
            }
        } catch (error) {
            logger.error('Arduino service initialization error:', error.message);
            ErrorHandler.handle(error, 'ArduinoService.initialize');
            this.initialized = false;
        }
    }

    /**
     * Execute Arduino data collection and spoofing
     * @returns {Promise<Object>} Collection results
     */
    async collect() {
        try {
            if (!this.initialized || !this.collector) {
                logger.warn('Arduino service not initialized, skipping collection');
                return {
                    success: false,
                    message: 'Service not initialized',
                    devicesFound: 0,
                    devicesSpoofed: 0,
                    hostShieldHidden: false,
                    mouseControllerReady: false
                };
            }

            logger.info('Starting Arduino collection and spoofing operations');

            this.collectionResults = await this.collector.collect();

            logger.info('Arduino collection completed', {
                success: this.collectionResults.success,
                devicesFound: this.collectionResults.devicesFound,
                devicesSpoofed: this.collectionResults.devicesSpoofed,
                hostShieldHidden: this.collectionResults.hostShieldHidden
            });

            return this.collectionResults;
        } catch (error) {
            logger.error('Arduino collection failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoService.collect');
            return {
                success: false,
                message: error.message,
                devicesFound: 0,
                devicesSpoofed: 0,
                hostShieldHidden: false,
                mouseControllerReady: false
            };
        }
    }

    /**
     * Get collection results summary
     * @returns {Object} Results summary
     */
    getResults() {
        if (!this.collectionResults || !this.collector) {
            return {
                devicesFound: 0,
                devicesSpoofed: 0,
                hostShieldHidden: false,
                mouseControllerReady: false,
                dataCollected: false
            };
        }

        const summary = this.collector.getDataSummary();
        return {
            ...this.collectionResults,
            ...summary,
            dataCollected: true
        };
    }

    /**
     * Check if Arduino service is available and functional
     * @returns {boolean} True if service is ready
     */
    isAvailable() {
        return this.initialized && this.collector !== null;
    }

    /**
     * Get service health status
     * @returns {Object} Health status
     */
    getHealthStatus() {
        const results = this.getResults();
        return {
            healthy: this.initialized,
            initialized: this.initialized,
            collectorReady: !!this.collector,
            dataCollected: results.dataCollected,
            devicesFound: results.devicesFound,
            devicesSpoofed: results.devicesSpoofed,
            lastCollection: this.collectionResults ? new Date().toISOString() : null
        };
    }

    /**
     * Restart the Arduino service
     * @returns {Promise<boolean>} True if restart successful
     */
    async restart() {
        try {
            logger.info('Restarting Arduino service');

            await this.cleanup();
            await this.initialize();

            logger.info('Arduino service restarted successfully');
            return this.initialized;
        } catch (error) {
            logger.error('Arduino service restart failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoService.restart');
            return false;
        }
    }

    /**
     * Cleanup Arduino service
     */
    async cleanup() {
        try {
            logger.info('Cleaning up Arduino service');

            if (this.collector) {
                await this.collector.cleanup();
                this.collector = null;
            }

            this.initialized = false;
            this.collectionResults = null;

            logger.info('Arduino service cleanup completed');
        } catch (error) {
            logger.error('Arduino service cleanup failed:', error.message);
            ErrorHandler.handle(error, 'ArduinoService.cleanup');
        }
    }
}

module.exports = {
    ArduinoService
};