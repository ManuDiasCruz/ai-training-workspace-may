import { testRepository } from "../repositories/testRepository.js";

async function deleteData(){
    return testRepository.resetDatabase();
}

export const testService = {
    deleteData
}
