import json
import os
import secrets


def generate_password():
    return secrets.token_hex(64)


def generate(orgs):
    files = {}

    # TODO merge two loops
    # init file content
    for org in orgs:
        data = {
            "incoming_organizations": [],
            "outgoing_organizations": [],
        }
        files[org] = data

    for org in orgs:
        # create intern organization (request from worker A to backend A)
        password = generate_password()
        files[org]["outgoing_organizations"].append({"organization_id": org, "secret": password})
        files[org]["incoming_organizations"].append({"organization_id": org, "password": password})

        other_orgs = [x for x in orgs if x != org]
        for other_org in other_orgs:
            # outgoing from server B to server A share same secret as incoming from server B in server A
            password = generate_password()
            files[other_org]["outgoing_organizations"].append(
                {"organization_id": org, "secret": password}
            )  # in server B  # to server A

            files[org]["incoming_organizations"].append(
                {"organization_id": other_org, "password": password}  # in server A  # from server B
            )

    return files


def generate_for_orgs(orgs):
    files = generate(orgs)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    organizations_path = os.path.join(dir_path, "organizations")
    os.makedirs(organizations_path, exist_ok=True)
    for k, v in files.items():
        filepath = os.path.join(organizations_path, f"{k}.json")
        with open(filepath, "w") as f:
            f.write(json.dumps(v, indent=4))


if __name__ == "__main__":
    orgs = ["owkinMSP", "chu-nantesMSP", "clbMSP"]  # TODO should be discovered by discovery service

    generate_for_orgs(orgs)
