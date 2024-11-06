from arcgis.gis import GIS
import keyring
import re
import os


def main():

    # This uses keyring to access credentials contained in Windows Credential manager
    agol_service = '' # Windows credential manager name
    agol_url = '' # typically https://arcgis.com

    itemID = ''
    output_folder = ''
    layerID = 0
    naming_column = '' # Feature service column used to name subfolders containing attachments

    portal = ArcGIS_Authenticate(agol_service,
                                 agol_url)

    get_attachments(portal=portal,
                    item_id=itemID,
                    output_folder=output_folder,
                    subfolder_column=naming_column,
                    layer_id=layerID)


def get_attachments(portal: GIS, item_id: str,
                    output_folder: str,
                    oid_field: str = 'objectid',
                    subfolder_column: str = None,
                    layer_id: int = 0):

    """saves attachments out of feature layer

    Args:
        portal (GIS): GIS object
        item_id (str): item id of feature layer in portal
        output_folder (str): folder path to save attachments
        oid_field (str, optional): name of objectid column in layer.
                                   Defaults to 'objectid'.
        subfolder_column (str, optional): use column with unique ids
                                          in feature layer to name
                                          folders under output_folder.
                                          Defaults to None.
        layer_id (int, optional): layer id if grouped. Defaults to 0.
    """
    item = portal.content.get(item_id)
    featureLayer = item.layers[layer_id]
    featureSet = featureLayer.query(where='1=1', out_fields='*')
    totalFeatures = len(featureSet)
    root_folder = output_folder

    for i, feature in enumerate(featureSet, start=1):
        oid = feature.attributes[oid_field]
        if subfolder_column:
            subfolder = sanitize_windows_path(feature.attributes[subfolder_column])
            full_output_folder = os.path.join(root_folder,
                                              subfolder)
        else:
            full_output_folder = root_folder
        full_output_folder = full_output_folder.rstrip()
        print(full_output_folder)
        print(f'downloading attachments feature {i}/{totalFeatures}')
        attachments = featureLayer.attachments.get_list(oid=oid)
        for attachment in attachments:
            attachmentID = attachment['id']
            attachmentName = attachment['name']
            print(f'downloading {attachmentName}')
            if os.path.exists(os.path.join(full_output_folder,
                                           attachmentName)):
                full_output_folder_s = os.path.join(full_output_folder,
                                                    str(attachmentID))
                print((f'{attachmentName} exists,'
                       f'saving to {full_output_folder_s}'))
                featureLayer.attachments.download(oid=oid,
                                                  attachment_id=attachmentID,
                                                  save_path=full_output_folder_s)
            else:
                featureLayer.attachments.download(oid=oid,
                                                  attachment_id=attachmentID,
                                                  save_path=full_output_folder)


def sanitize_windows_path(s: str) -> str:
    """removes windows path illegal characters from string

    Args:
        s (str): string to check

    Returns:
        str: _description_
    """
    illegal_chars = r'[<>:"/|?*]'
    sanitized_s = re.sub(illegal_chars, '', s)
    return sanitized_s


def ArcGIS_Authenticate(keyring_service: str,
                        portal_name: str):
    cred = keyring.get_credential(keyring_service, '')
    conn = GIS(url=portal_name,
               username=cred.username,
               password=cred.password)
    print("Successfully logged into '{}' via the '{}' user".format(
           conn.properties.portalHostname,
           conn.properties.user.username))
    return conn


if __name__ == '__main__':
    main()
