DROP SCHEMA IF EXISTS pydbreport;
CREATE SCHEMA `pydbreport` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin ;

CREATE  TABLE `pydbreport`.`famous_people` (
  `id` INT NOT NULL AUTO_INCREMENT ,
  `first_name` VARCHAR(150) NULL ,
  `last_name` VARCHAR(155) NULL ,
  `rating` INT NULL ,
  PRIMARY KEY (`id`) );


INSERT INTO `pydbreport`.`famous_people` (`first_name`, `last_name`, `rating`) VALUES ('Luke', 'Skywalker', '10');
INSERT INTO `pydbreport`.`famous_people` (`first_name`, `last_name`, `rating`) VALUES ('Master', 'Yoda', '20');
INSERT INTO `pydbreport`.`famous_people` (`first_name`, `last_name`, `rating`) VALUES ('Bruno', 'Diaz', '15');
INSERT INTO `pydbreport`.`famous_people` (`first_name`, `last_name`, `rating`) VALUES ('Clark', 'Kent', '1');
INSERT INTO `pydbreport`.`famous_people` (`first_name`, `last_name`, `rating`) VALUES ('wéirdnámé', 'ñaéd', '1');
