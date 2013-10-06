CREATE SCHEMA `pydbreport` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin ;

CREATE  TABLE `pydbreport`.`famous_people` (
  `id` INT NOT NULL ,
  `first_name` VARCHAR(150) NULL ,
  `last_name` VARCHAR(155) NULL ,
  `rating` INT NULL ,
  PRIMARY KEY (`id`) );


INSERT INTO `pydbreport`.`famous_people` (`id`, `first_name`, `last_name`, `rating`) VALUES (0, 'Luke', 'Skywalker', '10');
INSERT INTO `pydbreport`.`famous_people` (`id`,`first_name`, `last_name`, `rating`) VALUES (1, 'Master', 'Yoda', '20');
INSERT INTO `pydbreport`.`famous_people` (`id`,`first_name`, `last_name`, `rating`) VALUES (2, 'Bruno', 'Diaz', '15');
INSERT INTO `pydbreport`.`famous_people` (`id`,`first_name`, `last_name`, `rating`) VALUES (3, 'Clark', 'Kent', '1');
