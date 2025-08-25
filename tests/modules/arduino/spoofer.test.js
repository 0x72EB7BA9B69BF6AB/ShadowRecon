/**
 * Arduino Spoofer Tests
 * Test suite for Arduino device spoofing functionality
 */

const { ArduinoSpoofer } = require('../../../src/modules/arduino/spoofer');

describe('ArduinoSpoofer', () => {
    let spoofer;

    beforeEach(() => {
        spoofer = new ArduinoSpoofer();
    });

    afterEach(async () => {
        if (spoofer) {
            await spoofer.cleanup();
        }
    });

    describe('Initialization', () => {
        test('should initialize successfully', async () => {
            const result = await spoofer.initialize();
            expect(result).toBe(true);
            expect(spoofer.connectedDevices).toBeDefined();
            expect(spoofer.spoofedDevices).toBeDefined();
        });

        test('should detect platform correctly', () => {
            expect(spoofer.isWindows).toBe(process.platform === 'win32');
            expect(spoofer.isLinux).toBe(process.platform === 'linux');
            expect(spoofer.isMacOS).toBe(process.platform === 'darwin');
        });
    });

    describe('Device Detection', () => {
        test('should detect device types correctly', () => {
            const testCases = [
                { id: 'USB\\VID_2341&PID_0043', name: 'Arduino Uno', description: 'Arduino', expected: 'arduino' },
                { id: 'USB\\VID_1234&PID_5678', name: 'USB Host Shield', description: 'USB Host Shield', expected: 'usb_host_shield' },
                { id: 'USB\\VID_ABCD&PID_EFGH', name: 'Generic HID', description: 'Mouse', expected: 'hid_device' },
                { id: 'USB\\VID_1111&PID_2222', name: 'Generic USB', description: 'USB Device', expected: 'usb_device' }
            ];

            testCases.forEach(testCase => {
                const result = spoofer.detectDeviceType(testCase.id, testCase.name, testCase.description);
                expect(result).toBe(testCase.expected);
            });
        });
    });

    describe('Device Spoofing', () => {
        test('should generate spoofed device names', () => {
            const device = { id: 'test', name: 'Arduino Uno', type: 'arduino' };
            const spoofedName = spoofer.generateSpoofedName(device);
            
            expect(spoofedName).toBeDefined();
            expect(typeof spoofedName).toBe('string');
            expect(spoofedName.length).toBeGreaterThan(0);
            expect(spoofedName).not.toContain('Arduino');
        });

        test('should generate spoofed device descriptions', () => {
            const device = { id: 'test', name: 'Arduino Uno', type: 'arduino' };
            const spoofedDesc = spoofer.generateSpoofedDescription(device);
            
            expect(spoofedDesc).toBeDefined();
            expect(typeof spoofedDesc).toBe('string');
            expect(spoofedDesc.length).toBeGreaterThan(0);
        });

        test('should handle device spoofing for non-existent device', async () => {
            await spoofer.initialize();
            const result = await spoofer.spoofDevice('non-existent-device');
            expect(result).toBe(false);
        });
    });

    describe('Mouse Controller', () => {
        test('should initialize mouse controller when USB Host Shield present', async () => {
            // Add a mock USB Host Shield device
            spoofer.connectedDevices.set('test-shield', {
                id: 'test-shield',
                name: 'USB Host Shield',
                type: 'usb_host_shield',
                platform: 'test'
            });

            const result = await spoofer.initializeMouseController();
            expect(result).toBe(true);
            expect(spoofer.mouseController).toBeDefined();
            expect(spoofer.mouseController.initialized).toBe(true);
        });

        test('should fail to initialize mouse controller without USB Host Shield', async () => {
            const result = await spoofer.initializeMouseController();
            expect(result).toBe(false);
            expect(spoofer.mouseController).toBeNull();
        });

        test('should handle mouse movement commands', async () => {
            // Setup mock mouse controller
            spoofer.mouseController = {
                initialized: true,
                position: { x: 0, y: 0 },
                buttons: { left: false, right: false, middle: false },
                shieldDevice: { id: 'test-shield' }
            };

            const result = await spoofer.moveMouse(10, 20);
            expect(result).toBe(true);
            expect(spoofer.mouseController.position.x).toBe(10);
            expect(spoofer.mouseController.position.y).toBe(20);
        });

        test('should handle mouse click commands', async () => {
            // Setup mock mouse controller
            spoofer.mouseController = {
                initialized: true,
                position: { x: 0, y: 0 },
                buttons: { left: false, right: false, middle: false },
                shieldDevice: { id: 'test-shield' }
            };

            const result = await spoofer.clickMouse('left', true);
            expect(result).toBe(true);
            expect(spoofer.mouseController.buttons.left).toBe(true);
        });

        test('should fail mouse operations without initialized controller', async () => {
            const moveResult = await spoofer.moveMouse(10, 20);
            const clickResult = await spoofer.clickMouse('left', true);
            
            expect(moveResult).toBe(false);
            expect(clickResult).toBe(false);
        });
    });

    describe('Device Output Parsing', () => {
        test('should parse Windows device output correctly', () => {
            const mockOutput = `Node,Description,DeviceID,Name
,USB Root Hub,USB\\ROOT_HUB30\\4&1234,USB Root Hub
,Arduino Uno,USB\\VID_2341&PID_0043\\123456,Arduino Uno Rev3
,USB Host Shield,USB\\VID_1234&PID_HOST\\789012,USB Host Shield v2.0`;

            const devices = spoofer.parseWindowsDeviceOutput(mockOutput);
            
            expect(devices).toHaveLength(2); // Root hub should be filtered out
            expect(devices[0].name).toBe('Arduino Uno Rev3');
            expect(devices[0].type).toBe('arduino');
            expect(devices[1].name).toBe('USB Host Shield v2.0');
            expect(devices[1].type).toBe('usb_host_shield');
        });

        test('should parse Linux device output correctly', () => {
            const mockOutput = `Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 002: ID 2341:0043 Arduino SA Uno Rev3
Bus 002 Device 003: ID 1234:5678 Generic USB Host Shield`;

            const devices = spoofer.parseLinuxDeviceOutput(mockOutput);
            
            expect(devices).toHaveLength(3);
            expect(devices[1].name).toBe('Arduino SA Uno Rev3');
            expect(devices[1].type).toBe('arduino');
            expect(devices[2].name).toBe('Generic USB Host Shield');
            expect(devices[2].type).toBe('usb_host_shield');
        });
    });

    describe('Spoofing Status', () => {
        test('should return correct spoofing status', async () => {
            await spoofer.initialize();
            
            const status = spoofer.getSpoofingStatus();
            
            expect(status).toHaveProperty('totalDevices');
            expect(status).toHaveProperty('spoofedDevices');
            expect(status).toHaveProperty('hostShieldHidden');
            expect(status).toHaveProperty('mouseControllerReady');
            expect(status).toHaveProperty('platform');
            expect(status).toHaveProperty('devices');
            expect(status.platform).toBe(process.platform);
        });
    });

    describe('Cleanup', () => {
        test('should cleanup all spoofed devices', async () => {
            await spoofer.initialize();
            
            // Add mock spoofed device
            spoofer.spoofedDevices.set('test-device', {
                originalId: 'test-device',
                spoofedId: 'spoofed-test',
                type: 'arduino'
            });

            await spoofer.cleanup();
            
            expect(spoofer.spoofedDevices.size).toBe(0);
            expect(spoofer.mouseController).toBeNull();
            expect(spoofer.hostShieldHidden).toBe(false);
        });
    });
});