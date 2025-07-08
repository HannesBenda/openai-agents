import asyncio
import os
from openai import AsyncOpenAI
import json
from tools import tools, agentTools
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

BASE_URL = "http://188.245.32.59:4000"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

API_URL = "http://localhost:8081/task/index/" 
LOG_FILE = "results.log"

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

async def run_agents(index):
    api_url = f"{API_URL}{index}"
    print(f"fetching test case {index} from {api_url}...")
    local_repo = os.path.join(os.getcwd(), f"repos/repo_{index}")
    local_repo = local_repo.replace("\\", '/')
    work_dir = os.getcwd()

    try:
        testcase = tools.fetch_test_case(api_url)
        prompt = testcase["Problem_statement"]
        git_clone = testcase["git_clone"]
        fail_tests = json.loads(testcase.get("FAIL_TO_PASS", "[]"))
        pass_tests = json.loads(testcase.get("PASS_TO_PASS", "[]"))
        instance_id = testcase["instance_id"]
        try:
            tools.clone_repo(git_clone, local_repo)
        except Exception as e:
            print(f"Git repo is already cloned")

        # basic prompt
        prompt = (
            f"You are a team of agents with the following roles:\n"
            f"- Planner: breaks down the problem into coding tasks\n"
            f"- Coder: makes actual changes to the code files in the Git repository\n"
            # give the repository information
            f"Work in the directory: repo_{index}. This is a Git repository.\n"
            f"The absolute path to the Git repository is {local_repo}.\n"
            f"Your goal is to fix the problem described below.\n"
            f"All code changes must be saved to the files, so they appear in `git diff`.\n"
            f"Problem description:\n"
            f"{prompt}\n\n"
            # most important information bc LLM doesn't care for earlier instructions
            f"IMPORTANT: Make sure the fix is minimal and only touches what's necessary without removing any other funcitonality from the code.\n"
            f"You must keep all content of the file that might still be working.\n"
            f"If you propose to change a few lines within a code file, you must keep all other code and incorporate it into your file_content response.\n"
        
        )
        # instrucitons for specific agent
        instructions = (
            f"You are a bug-fixing specialist. Follow this workflow:\n\n"
            f"1. Search for the file and its path in the repository that needs to be edited or created.\n"
            f"2. Analyze the file's content using the read_file tool.\n"
            f"3. Identify which part of the file needs to be edited.\n"
            f"4. Integrate the adapted code part into the whole code file in order to only change a small portion of the content.\n"
            f"5. If a directory that needs to be created does not exist, only then use the create_directory tool to create it.\n"
            f"6. Update the files content using the write_file tool. Only overwrite the content that needs to be edited and supply the rest of the code unchanged.\n"
            f"7. Execute the code change at most after two iterations of thinking about it.\n\n"
            f"IMPORTANT: Make sure that you only update the code parts that are required and keep all other code.\n"
        )
        agent = Agent(
            name="Agent",
            instructions=instructions,
            model=MODEL,
            tools=[
                agentTools.read_file_content,
                agentTools.write_file_content,
                agentTools.create_directory,
                agentTools.get_current_working_directory
            ],
        )
        #run agent
        result = await Runner.run(agent, prompt, max_turns = 30)
        #print(f"Agent result: {result}")

        #Call REST service instead for evaluation changes form agent
        print(f"Calling SWE-Bench REST service with repo: {local_repo}")
        test_payload = {
            "instance_id": instance_id,
            "repoDir": f"/repos/repo_{index}", #mount with docker
            "FAIL_TO_PASS": fail_tests,
            "PASS_TO_PASS": pass_tests,
        }
        #print(f"test_payload: {test_payload}")
        result_json = tools.verify_solution(test_payload)
        #print(f"result_json:\n{result_json}")
        tools.log_results(result_json, work_dir, LOG_FILE, index, 0)
        

    except Exception as e:
        os.chdir(work_dir)
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"\n--- TESTCASE {index} ---\n")
            log.write(f"Error: {e}")
        print(f"Error in test case {index}: {e}")


async def main():
    for i in range(1,2):
        await run_agents(i)

if __name__ == "__main__":
    asyncio.run(main())
