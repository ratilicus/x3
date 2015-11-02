from x3lib import *

class BulletObj(BaseObj):
    TEMPLATE = (
        "Model file",
        "Picture ID",
        "Rotation X",
        "Rotation Y",
        "Rotation Z",
        "Subtype",
        "Description",
        "Shield Damage",
        "Energy Used",
        "Impact Sound",
        "Lifetime",
        "Speed",
        "Flags",
        "Color R",
        "Color G",
        "Color B",
        "width",
        "height",
        "length",
        "Trail Effect",
        "Impact Effect",
        "Launch Effect",
        "Hull Damage",
        "Engine Trail",
        "Ambiend Sound",
        "Sound Volume (max)",
        "Sound Volume (min)",
        "Launch Delay",
        "Speed Reduce (percent)",
        "Speed Reduce (duration)",
        "Target Weapon Drain",
        "Damage over Time (energy)",
        "Damage over Time (duration)",
        "Fragment Bullet Index",
        "Number of Fragments",
        "Charged Energy Amplifier",
        "Charged Size Amplifier",
        "OOS Shield Damage",
        "OOS Hull Damage",
        "Ammo TWareT Index",
        "Relative Value",
        "Price modifier 1",
        "Price modifier 2",
        "Size",
        "Relative value (player)",
        "Minimum Notoriety",
        "Video ID",
        "Skin Index",
        "ID",
    )


class LaserObj(BaseObj):
    TEMPLATE = (
        "Model file",
        "Picture ID",
        "Rotation X",
        "Rotation Y",
        "Rotation Z",
        "Subtype",
        "Description",
        "Rate of fire",
        "Sound",
        "Projectile",
        "Energy",
        "Charge rate",
        "Icon",
        "Volume",
        "Relative Value",
        "Price modifier 1",
        "Price modifier 2",
        "Size",
        "Relative value (player)",
        "Minimum Notoriety",
        "Video ID",
        "Skin Index",
        "ID",
    )


if __name__ == '__main__':

    print "Getting bullets"
    lines=open('ap/addon/types/tbullets.pck').readlines()[3:]
    bullets = []
    for line in lines:
        data = line.strip().split(';')
        if len(data) < 10:
            continue
        bullets.append(BulletObj(data))

    print "Getting lasers"
    lines=open('ap/addon/types/tlaser.pck').readlines()[2:]
    lasers = []
    for line in lines:
        data = line.strip().split(';')
        if len(data) < 10:
            continue
        lasers.append(LaserObj(data))


    print "Getting pages"
    pages = Pages()

    import pymongo
    mongo=pymongo.MongoClient()
    db=mongo.x3

    db.bullets.drop()
    for id, o in enumerate(bullets):
            o.data['_id']=o.data['line']=id
            db.bullets.save(o.data)

    page_id = 17
    db.lasers.drop()
    for id, o in enumerate(lasers):
        o.data['_id']=o.data['line']=id

        t_id=o.data['description']
        o.data['laser_name'] = pages.get_page(page_id, t_id)
        o.data['laser_desc'] = pages.get_page(page_id, t_id+1)

        o.data['bullet']=bullet=bullets[o.data['projectile']].data

        fire_rate = 1000.0/o.data['rate_of_fire']
        speed = bullet['speed']/500.0
        o.data['info'] = dict(
            fire_rate=round(fire_rate, 1),
            speed=round(speed, 0),
            range=round(speed * bullet['lifetime'] / 1000.0, 0),
            dps_hull=round(bullet['hull_damage']*fire_rate, 0),
            dps_shields=round(bullet['shield_damage']*fire_rate, 0),
            eps=round(bullet['energy_used']*fire_rate, 0),
            flags=get_bullet_flags(bullet['flags'])
        )
        db.lasers.save(o.data)
