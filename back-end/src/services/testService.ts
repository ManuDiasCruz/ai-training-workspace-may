import { testRepository } from "../repositories/testRepository";

async function deleteData(){
    return testRepository.resetDatabase();
}

export const testService = {
    deleteData
}