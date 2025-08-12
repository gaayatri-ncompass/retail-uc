const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');


const dbConfig = {
    host: 'localhost',
    user: 'root',
    password: 'deva',
    database: 'stagingdb'
};

const fakeNames = [
    'James Smith', 'Mary Johnson', 'Robert Williams', 'Patricia Brown', 'John Jones',
    'Jennifer Garcia', 'Michael Miller', 'Linda Davis', 'William Rodriguez', 'Elizabeth Martinez',
    'David Wilson', 'Barbara Anderson', 'Richard Taylor', 'Susan Thomas', 'Joseph Jackson',
    'Jessica White', 'Thomas Harris', 'Sarah Martin', 'Christopher Garcia', 'Nancy Martinez',
    'Daniel Robinson', 'Lisa Clark', 'Matthew Rodriguez', 'Betty Lewis', 'Anthony Lee',
    'Helen Walker', 'Mark Hall', 'Sandra Allen', 'Donald Young', 'Donna Hernandez',
    'Steven King', 'Carol Wright', 'Paul Lopez', 'Ruth Hill', 'Andrew Scott',
    'Sharon Green', 'Joshua Adams', 'Michelle Baker', 'Kenneth Gonzalez', 'Laura Nelson',
    'Kevin Carter', 'Emily Mitchell', 'Brian Perez', 'Kimberly Roberts', 'George Turner',
    'Deborah Phillips', 'Edward Campbell', 'Dorothy Parker', 'Ronald Evans', 'Lisa Edwards'
];

const fakeProductNames = [
    'Premium', 'Deluxe', 'Classic', 'Ultra', 'Special', 'Original', 'Fresh', 'Natural',
    'Organic', 'Supreme', 'Elite', 'Professional', 'Standard', 'Gourmet', 'Traditional',
    'Modern', 'Advanced', 'Basic', 'Essential', 'Quality', 'Pure', 'Rich', 'Light',
    'Strong', 'Mild', 'Sweet', 'Spicy', 'Crispy', 'Smooth', 'Creamy'
];

const categories = ['Snacks', 'Beverages', 'Dairy', 'Meat', 'Produce', 'Bakery', 'Frozen', 'Canned'];

const cities = [
    'Springfield', 'Franklin', 'Georgetown', 'Clinton', 'Fairview', 'Madison', 'Washington',
    'Chester', 'Marion', 'Oxford', 'Salem', 'Milton', 'Riverside', 'Greenwood', 'Bristol',
    'Kingston', 'Auburn', 'Manchester', 'Newport', 'Burlington', 'Jackson', 'Arlington',
    'Richmond', 'Troy', 'Clayton', 'Hudson', 'Wayne', 'Dover', 'Lancaster', 'Ashland'
];

const states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'];

function getRandomElement(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function generateRandomId(prefix, num) {
    return `${prefix}${num}`;
}

function generateRandomEmail(name) {
    const domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com', 'business.net'];
    const cleanName = name.toLowerCase().replace(/[^a-z]/g, '');
    const randomNum = Math.floor(Math.random() * 999);
    return `${cleanName}${randomNum}@${getRandomElement(domains)}`;
}

function generateRandomPhone() {
    const formats = [
        `(${String(Math.floor(Math.random() * 900) + 100)})${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}x${String(Math.floor(Math.random() * 90000) + 10000)}`,
        `+1-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 900) + 100)}-${String(Math.floor(Math.random() * 9000) + 1000)}`,
        `${String(Math.floor(Math.random() * 9000000000) + 1000000000)}`
    ];
    return getRandomElement(formats);
}

function generateRandomAddress() {
    const streetNumbers = Math.floor(Math.random() * 9999) + 1;
    const streetNames = ['Main St', 'Oak Ave', 'Pine Rd', 'Elm Dr', 'Cedar Ln', 'Park Blvd', 'Hill St', 'Lake Dr', 'River Rd', 'Valley Ave'];
    const streetTypes = ['Street', 'Avenue', 'Road', 'Drive', 'Lane', 'Court', 'Place', 'Way', 'Circle', 'Boulevard'];
    const suiteTypes = ['Suite', 'Apt', 'Unit'];
    
    let address = `${streetNumbers} ${getRandomElement(fakeNames.map(n => n.split(' ')[1]))} ${getRandomElement(streetTypes)}`;
    
    if (Math.random() > 0.7) {
        address += ` ${getRandomElement(suiteTypes)} ${String(Math.floor(Math.random() * 999) + 1).padStart(3, '0')}`;
    }
    
    const city = `${Math.random() > 0.5 ? 'New ' : ''}${getRandomElement(cities)}${Math.random() > 0.8 ? 'ville' : ''}`;
    const state = getRandomElement(states);
    const zip = String(Math.floor(Math.random() * 90000) + 10000);
    
    return `"${address}, ${city}, ${state} ${zip}"`;
}

function generateRandomDate(startYear = 2026, endYear = 2027) {
    const start = new Date(startYear, 0, 1);
    const end = new Date(endYear, 11, 31);
    const randomTime = start.getTime() + Math.random() * (end.getTime() - start.getTime());
    return new Date(randomTime).toISOString().split('T')[0];
}

function generateRandomPrice() {
    return (Math.random() * 1000 + 50).toFixed(2);
}

function generateRandomQuantity() {
    return Math.floor(Math.random() * 10) + 1;
}

function generateRandomStockLevel() {
    return Math.floor(Math.random() * 1000) + 50;
}

function generateProductsData(startId, count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        const id = generateRandomId('PROD', startId + i);
        const name = getRandomElement(fakeProductNames);
        const category = getRandomElement(categories);
        const price = generateRandomPrice();
        data.push(`${id},${name},${category},${price}`);
    }
    return data;
}

function generateCustomersData(startId, count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        const id = generateRandomId('CUST', startId + i);
        const name = getRandomElement(fakeNames);
        const email = generateRandomEmail(name);
        const phone = generateRandomPhone();
        const address = generateRandomAddress();
        const signupDate = generateRandomDate();
        data.push(`${id},${name},${email},${phone},${address},${signupDate}`);
    }
    return data;
}

function generateInventoryData(startProductId, startStoreId, startSupplierId, count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        const productId = generateRandomId('PROD', Math.floor(Math.random() * 500) + startProductId);
        const storeId = generateRandomId('STORE', Math.floor(Math.random() * 100) + startStoreId);
        const stockLevel = generateRandomStockLevel();
        const lastUpdated = generateRandomDate(2026, 2027);
        const supplierId = generateRandomId('SUP', Math.floor(Math.random() * 200) + startSupplierId);
        data.push(`${productId},${storeId},${stockLevel},${lastUpdated},${supplierId}`);
    }
    return data;
}

function generateSalesData(startSaleId, startCustomerId, startProductId, startStoreId, count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        const saleId = generateRandomId('SALE', startSaleId + i);
        const customerId = generateRandomId('CUST', Math.floor(Math.random() * 9000) + startCustomerId);
        const productId = generateRandomId('PROD', Math.floor(Math.random() * 500) + startProductId);
        const storeId = generateRandomId('STORE', Math.floor(Math.random() * 100) + startStoreId);
        const saleDate = generateRandomDate(2026, 2027);
        const quantity = generateRandomQuantity();
        const totalAmount = (parseFloat(generateRandomPrice()) * quantity).toFixed(2);
        data.push(`${saleId},${customerId},${productId},${storeId},${saleDate},${quantity},${totalAmount}`);
    }
    return data;
}

function generateStoresData(startId, count) {
    const data = [];
    for (let i = 0; i < count; i++) {
        const id = generateRandomId('STORE', startId + i);
        const storeName = `${getRandomElement(cities)} Store`;
        const location = `${Math.random() > 0.5 ? 'East ' : 'West '}${getRandomElement(cities)}${Math.random() > 0.7 ? 'town' : ''}`;
        const manager = getRandomElement(fakeNames);
        data.push(`${id},${storeName},${location},${manager}`);
    }
    return data;
}

function generateSuppliersData(startId, count) {
    const data = [];
    const companyTypes = ['LLC', 'Ltd', 'Inc', 'Corp', 'Co'];
    const businessFormats = [
        '{name1} {type}',
        '{name1}, {name2} and {name3}',
        '{name1}-{name2}',
        '{name1} & {name2} {type}'
    ];
    
    for (let i = 0; i < count; i++) {
        const id = generateRandomId('SUP', startId + i);
        
        const name1 = fakeNames[Math.floor(Math.random() * fakeNames.length)].split(' ')[1];
        const name2 = fakeNames[Math.floor(Math.random() * fakeNames.length)].split(' ')[1];
        const name3 = fakeNames[Math.floor(Math.random() * fakeNames.length)].split(' ')[1];
        const type = getRandomElement(companyTypes);
        const format = getRandomElement(businessFormats);
        
        let companyName = format
            .replace('{name1}', name1)
            .replace('{name2}', name2)
            .replace('{name3}', name3)
            .replace('{type}', type);
            
        const contactName = getRandomElement(fakeNames);
        const contactEmail = generateRandomEmail(contactName);
        
        data.push(`${id},"${companyName}",${contactName},${contactEmail}`);
    }
    return data;
}

let counters = {
    products: 2200,
    customers: 10000,
    inventory: { product: 1000, store: 100, supplier: 100 },
    sales: { sale: 400000, customer: 1000, product: 1000, store: 100 },
    stores: 800,
    suppliers: 800
};

async function addSingleRecordToCSV(csvFile, counter) {
    const dataDir = '../data';
    const filePath = path.join(dataDir, csvFile.name);
    
    try {
        if (!fs.existsSync(filePath)) {
            console.log(`File ${filePath} does not exist. Skipping...`);
            return;
        }

        const newData = csvFile.generator(counter, 1);
        const dataToAppend = '\n' + newData.join('\n');
        fs.appendFileSync(filePath, dataToAppend);
        
        console.log(`Added 1 record to ${csvFile.name}`);
        
    } catch (error) {
        console.error(`Error processing ${csvFile.name}:`, error.message);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function getLatestCounters() {
    let counters = {
        products: 1000,
        customers: 1000,
        inventory: { product: 1000, store: 100, supplier: 100 },
        sales: { sale: 100000, customer: 1000, product: 1000, store: 100 },
        stores: 100,
        suppliers: 100
    };

    try {
        
        const dataDir = '../data';
        
        
        if (fs.existsSync(path.join(dataDir, 'customers.csv'))) {
            const customerData = fs.readFileSync(path.join(dataDir, 'customers.csv'), 'utf8');
            const customerLines = customerData.trim().split('\n');
            if (customerLines.length > 1) {
                const lastCustomer = customerLines[customerLines.length - 1].split(',')[0];
                const customerNumber = parseInt(lastCustomer.replace('CUST', ''));
                if (!isNaN(customerNumber)) {
                    counters.customers = customerNumber + 1;
                    console.log(`📊 Latest customer ID: ${lastCustomer} -> Next: CUST${counters.customers}`);
                }
            }
        }

        // Check products
        if (fs.existsSync(path.join(dataDir, 'products.csv'))) {
            const productData = fs.readFileSync(path.join(dataDir, 'products.csv'), 'utf8');
            const productLines = productData.trim().split('\n');
            if (productLines.length > 1) {
                const lastProduct = productLines[productLines.length - 1].split(',')[0];
                const productNumber = parseInt(lastProduct.replace('PROD', ''));
                if (!isNaN(productNumber)) {
                    counters.products = productNumber + 1;
                    console.log(`📊 Latest product ID: ${lastProduct} -> Next: PROD${counters.products}`);
                }
            }
        }

        // Check sales
        if (fs.existsSync(path.join(dataDir, 'sales.csv'))) {
            const salesData = fs.readFileSync(path.join(dataDir, 'sales.csv'), 'utf8');
            const salesLines = salesData.trim().split('\n');
            if (salesLines.length > 1) {
                const lastSale = salesLines[salesLines.length - 1].split(',')[0];
                const salesNumber = parseInt(lastSale.replace('SALE', ''));
                if (!isNaN(salesNumber)) {
                    counters.sales.sale = salesNumber + 1;
                    console.log(`📊 Latest sales ID: ${lastSale} -> Next: SALE${counters.sales.sale}`);
                }
            }
        }

        // Check stores
        if (fs.existsSync(path.join(dataDir, 'stores.csv'))) {
            const storeData = fs.readFileSync(path.join(dataDir, 'stores.csv'), 'utf8');
            const storeLines = storeData.trim().split('\n');
            if (storeLines.length > 1) {
                const lastStore = storeLines[storeLines.length - 1].split(',')[0];
                const storeNumber = parseInt(lastStore.replace('STORE', ''));
                if (!isNaN(storeNumber)) {
                    counters.stores = storeNumber + 1;
                    console.log(`📊 Latest store ID: ${lastStore} -> Next: STORE${counters.stores}`);
                }
            }
        }

        // Check suppliers
        if (fs.existsSync(path.join(dataDir, 'suppliers.csv'))) {
            const supplierData = fs.readFileSync(path.join(dataDir, 'suppliers.csv'), 'utf8');
            const supplierLines = supplierData.trim().split('\n');
            if (supplierLines.length > 1) {
                const lastSupplier = supplierLines[supplierLines.length - 1].split(',')[0];
                const supplierNumber = parseInt(lastSupplier.replace('SUP', ''));
                if (!isNaN(supplierNumber)) {
                    counters.suppliers = supplierNumber + 1;
                    console.log(`📊 Latest supplier ID: ${lastSupplier} -> Next: SUP${counters.suppliers}`);
                }
            }
        }

        
        return counters;

    } catch (error) {
        console.log(` Could not read CSV files: ${error.message}`);
        
        return counters;
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function continuousDataGeneration() {
    
    let counters = await getLatestCounters();
    
    const csvFiles = [
        { 
            name: 'products.csv', 
            generator: generateProductsData, 
            getParams: () => [counters.products++, 1] 
        },
        { 
            name: 'customers.csv', 
            generator: generateCustomersData, 
            getParams: () => [counters.customers++, 1] 
        },
        { 
            name: 'inventory.csv', 
            generator: generateInventoryData, 
            getParams: () => [counters.inventory.product, counters.inventory.store, counters.inventory.supplier, 1] 
        },
        { 
            name: 'sales.csv', 
            generator: generateSalesData, 
            getParams: () => [counters.sales.sale++, counters.sales.customer, counters.sales.product, counters.sales.store, 1] 
        },
        { 
            name: 'stores.csv', 
            generator: generateStoresData, 
            getParams: () => [counters.stores++, 1] 
        },
        { 
            name: 'suppliers.csv', 
            generator: generateSuppliersData, 
            getParams: () => [counters.suppliers++, 1] 
        }
    ];

    while (true) {
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] Adding records...`);
        
        for (const csvFile of csvFiles) {
            const dataDir = '../data';
            const filePath = path.join(dataDir, csvFile.name);
            
            try {
                if (!fs.existsSync(filePath)) {
                    console.log(`File ${filePath} does not exist. Skipping...`);
                    continue;
                }

                const params = csvFile.getParams();
                const newData = csvFile.generator(...params);
                const dataToAppend = '\n' + newData.join('\n');
                fs.appendFileSync(filePath, dataToAppend);
                
            } catch (error) {
                console.error(`Error processing ${csvFile.name}:`, error.message);
            }
        }
        
        await sleep(1000);
    }
}

continuousDataGeneration().catch((error) => {
    console.error('Script failed:', error.message);
});