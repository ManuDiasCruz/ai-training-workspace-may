import { SeedOptions, testRepository } from "../repositories/testRepository.js";

async function deleteData(){
    return testRepository.resetDatabase();
}

async function seedData(options: SeedOptions){
    await testRepository.resetDatabase();

    return testRepository.seedDatabase(options);
}

export const testService = {
    deleteData,
    seedData
}
